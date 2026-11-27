"""The agent: upstream's turn-based text agent, with bla making the model calls.

``BlaAgent`` is upstream's ``LLMAgent`` with one method replaced, the model call. The system
prompt (``SYSTEM_PROMPT`` built from the policy), the tools and the way a conversation is kept
are upstream's. The call goes through bla's own provider code (``Send``), so that bla asks for
prompt caching and counts the tokens each reply reports, by kind.
"""

import contextvars
import hashlib
import json
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from ..providers import Send
from . import rules as retail_rules
from .upstream import AGENT_NAME, load

AGENT_MAX_TOKENS = 8192  # the Messages API requires a limit; a retail turn is a short message or a tool call
REFUSAL_STOP_REASONS = {"refusal"}
FIRST_MESSAGE_ERROR = "first message must use the"  # older Messages API versions reject a first assistant message
OPENING_USER_TEXT = "."


class AgentCallError(Exception):
    """The agent's model call failed or was refused: the conversation is unscored."""


@dataclass
class AgentCall:
    """One model call of the agent: the tokens the provider reported, by kind."""

    model: str | None
    uncached_input_tokens: int
    cache_write_input_tokens: int
    cache_read_input_tokens: int
    output_tokens: int
    stop_reason: str | None = None
    latency_seconds: float = 0.0
    usage_reported: bool = True  # False: the reply carried no usage or only part of it, so some zeros above are unknown, not measured

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


TOKEN_KINDS = ("uncached_input_tokens", "cache_write_input_tokens", "cache_read_input_tokens", "output_tokens")


@dataclass
class AgentUsage:
    """Every call the agent made in one attempt, kept even when the attempt fails."""

    calls: list[AgentCall] = field(default_factory=list)  # replies that arrived and could be read for usage
    dispatches: int = 0  # requests actually sent: transport retries and requests the API rejected count, replies or not
    opening_turn_added: bool = False  # the Anthropic retry that prepends a user turn happened
    messages: list[Any] = field(default_factory=list)  # the agent's view of the conversation so far, for a failed attempt
    checks: list[str] = field(default_factory=list)  # with ``--finish-check``: each time a reply was held and asked again, which check
    writes_checked: int = 0  # write calls of the conversation already covered by a requests check
    handover_offered: bool = False  # with ``--handover-rule``: the customer asked for a person, so the transfer tool was offered
    handover_refusals: int = 0  # with ``--handover-rule``: replies that announced a transfer without the tool and were asked again
    handover_announced: int = 0  # with ``--handover-rule``: replies that still announced one after the asks, and went to the customer
    rule_holds: list[str] = field(default_factory=list)  # with ``--rules``: each reply held and asked again, by rule
    address_corrections: int = 0  # with ``--rules address``: address calls whose country or state was put in the database's form

    def totals(self) -> dict[str, int]:
        return {kind: sum(getattr(call, kind) for call in self.calls) for kind in TOKEN_KINDS}

    def calls_without_usage(self) -> int:
        """Requests whose tokens are unknown: sent, but no reply with usage came back."""
        return self.dispatches - sum(1 for call in self.calls if call.usage_reported)

    def models(self) -> list[str]:
        return list(dict.fromkeys(call.model for call in self.calls if call.model))


def tool_definitions(tools: list[Any]) -> list[dict[str, Any]]:
    """Upstream's own (OpenAI-format) schema of each tool, unchanged."""
    return [tool.openai_schema for tool in tools]


# --- conversation -> provider messages ---------------------------------------------------


def _messages(state_messages: list[Any]) -> list[dict[str, Any]]:
    """The conversation as plain role/content items; consecutive tool results stay separate."""
    upstream = load()  # noqa: F841  (imported for its side effect: the vendored path)
    from tau2.data_model.message import AssistantMessage, ToolMessage, UserMessage

    items: list[dict[str, Any]] = []
    for message in state_messages:
        if isinstance(message, UserMessage):
            items.append({"role": "user", "text": message.content or ""})
        elif isinstance(message, AssistantMessage):
            items.append({"role": "assistant", "text": message.content or "",
                          "calls": [{"id": c.id, "name": c.name, "arguments": c.arguments}
                                    for c in message.tool_calls or []]})
        elif isinstance(message, ToolMessage):
            items.append({"role": "tool", "id": message.id, "text": message.content or ""})
    return items


def openai_request(model: str, system: str, items: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    """The Responses API request: system prompt, upstream's tools, the conversation so far."""
    request_input: list[dict[str, Any]] = []
    for item in items:
        if item["role"] == "user":
            request_input.append({"role": "user", "content": item["text"]})
        elif item["role"] == "assistant":
            if item["text"]:
                request_input.append({"role": "assistant", "content": item["text"]})
            for call in item["calls"]:
                request_input.append({"type": "function_call", "call_id": call["id"], "name": call["name"],
                                      "arguments": json.dumps(call["arguments"])})
        else:
            request_input.append({"type": "function_call_output", "call_id": item["id"], "output": item["text"]})
    function_tools = [{"type": "function", "strict": False, **{k: t["function"][k] for k in ("name", "description", "parameters")}}
                      for t in tools]
    # OpenAI caches the longest shared prefix by itself; the key sends every conversation of a
    # run with the same system prompt and tools to the same cache.
    prefix = hashlib.sha256(json.dumps([system, function_tools], sort_keys=True).encode()).hexdigest()[:32]
    request: dict[str, Any] = {"model": model, "instructions": system, "input": request_input, "store": False,
                               "prompt_cache_key": f"bla-tau-{prefix}"}
    if function_tools:
        request["tools"] = function_tools
    return request


def anthropic_request(model: str, system: str, items: list[dict[str, Any]], tools: list[dict[str, Any]],
                      opening: bool = False) -> dict[str, Any]:
    """The Messages request, with cache breakpoints on the tools, the system prompt and the last message."""
    messages: list[dict[str, Any]] = []

    def add(role: str, blocks: list[dict[str, Any]]) -> None:
        if messages and messages[-1]["role"] == role:  # the API wants alternating roles; tool results share one turn
            messages[-1]["content"].extend(blocks)
        else:
            messages.append({"role": role, "content": list(blocks)})

    for item in items:
        if item["role"] == "user":
            add("user", [{"type": "text", "text": item["text"]}] if item["text"] else [])
        elif item["role"] == "assistant":
            blocks: list[dict[str, Any]] = [{"type": "text", "text": item["text"]}] if item["text"] else []
            blocks += [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["arguments"]} for c in item["calls"]]
            add("assistant", blocks)
        else:
            add("user", [{"type": "tool_result", "tool_use_id": item["id"], "content": item["text"]}])
    if opening and messages and messages[0]["role"] == "assistant":
        messages.insert(0, {"role": "user", "content": [{"type": "text", "text": OPENING_USER_TEXT}]})
    if messages and messages[-1]["content"]:
        messages[-1]["content"][-1] = {**messages[-1]["content"][-1], "cache_control": {"type": "ephemeral"}}
    request: dict[str, Any] = {
        "model": model, "max_tokens": AGENT_MAX_TOKENS, "messages": messages,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
    }
    anthropic_tools = [{"name": t["function"]["name"], "description": t["function"]["description"],
                        "input_schema": t["function"]["parameters"]} for t in tools]
    if anthropic_tools:
        anthropic_tools[-1] = {**anthropic_tools[-1], "cache_control": {"type": "ephemeral"}}
        request["tools"] = anthropic_tools
    return request


# --- provider reply -> upstream message --------------------------------------------------


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _complete(usage: dict[str, Any]) -> bool:
    """Both token totals were reported (cache details may be legitimately absent); a partial usage is not complete."""
    return all(isinstance(usage.get(k), int) and not isinstance(usage.get(k), bool) for k in ("input_tokens", "output_tokens"))

def parse_openai(reply: dict[str, Any]) -> tuple[str, list[dict[str, Any]], AgentCall]:
    try:
        if reply.get("status") not in (None, "completed"):
            raise AgentCallError(f"OpenAI response {reply.get('status')}: {reply.get('incomplete_details') or reply.get('error')}")
        texts: list[str] = []
        calls: list[dict[str, Any]] = []
        for item in reply["output"]:
            if item["type"] == "message":
                for part in item.get("content") or []:
                    if part.get("type") == "refusal":
                        raise AgentCallError(f"the model refused: {part.get('refusal')}")
                    if part.get("type") == "output_text":
                        texts.append(part["text"])
            elif item["type"] == "function_call":
                try:
                    arguments = json.loads(item["arguments"])
                except ValueError:
                    raise AgentCallError(f"arguments of {item['name']} are not valid JSON") from None
                if not isinstance(arguments, dict):
                    raise AgentCallError(f"arguments of {item['name']} are not a JSON object")
                calls.append({"id": item["call_id"], "name": item["name"], "arguments": arguments})
        usage = reply.get("usage") or {}
        cached = _int((usage.get("input_tokens_details") or {}).get("cached_tokens"))
        call = AgentCall(reply.get("model"), max(_int(usage.get("input_tokens")) - cached, 0), 0, cached,
                         _int(usage.get("output_tokens")), reply.get("status"), usage_reported=_complete(usage))
        return "".join(texts), calls, call
    except (KeyError, TypeError, AttributeError) as error:
        raise AgentCallError(f"unexpected OpenAI response shape: {type(error).__name__}: {error}") from None


def parse_anthropic(reply: dict[str, Any]) -> tuple[str, list[dict[str, Any]], AgentCall]:
    try:
        stop = reply.get("stop_reason")
        usage = reply.get("usage") or {}
        call = AgentCall(reply.get("model"), _int(usage.get("input_tokens")), _int(usage.get("cache_creation_input_tokens")),
                         _int(usage.get("cache_read_input_tokens")), _int(usage.get("output_tokens")), stop,
                         usage_reported=_complete(usage))
        if stop in REFUSAL_STOP_REASONS:
            raise AgentCallError("the model refused (stop reason: refusal)")
        if stop == "max_tokens":
            raise AgentCallError("the reply was cut off at the output limit")
        texts: list[str] = []
        calls: list[dict[str, Any]] = []
        for block in reply["content"]:
            if block["type"] == "text":
                texts.append(block["text"])
            elif block["type"] == "tool_use":
                if not isinstance(block["input"], dict):
                    raise AgentCallError(f"input of {block['name']} is not a JSON object")
                calls.append({"id": block["id"], "name": block["name"], "arguments": block["input"]})
        return "".join(texts), calls, call
    except (KeyError, TypeError, AttributeError) as error:
        raise AgentCallError(f"unexpected Anthropic response shape: {type(error).__name__}: {error}") from None


@dataclass(frozen=True)
class Attempt:
    """What the agent of the conversation running in this thread needs: provider, model, key, instruction."""

    provider: str
    model: str
    api_key: str
    send: Send
    usage: AgentUsage
    instruction: str | None = None
    finish_check: bool = False
    handover_rule: bool = False
    rules: tuple[str, ...] = ()


_attempt: contextvars.ContextVar[Attempt | None] = contextvars.ContextVar("tau_attempt", default=None)


@contextmanager
def attempting(attempt: Attempt) -> Any:
    token = _attempt.set(attempt)
    try:
        yield
    finally:
        _attempt.reset(token)


def counting(send: Send) -> Send:
    """``send`` that counts, in the running attempt, every request actually dispatched (put beneath the retries)."""

    def counted(provider: str, api_key: str, request: dict[str, Any]) -> dict[str, Any]:
        attempt = _attempt.get()
        if attempt is not None:
            attempt.usage.dispatches += 1
        return send(provider, api_key, request)

    return counted


# --- the finish check (``--finish-check``) -------------------------------------------------
#
# Off by default. With it, a reply of the agent is held once and the model is asked again, with a
# note, in two cases: the reply hands the customer to a human, or it is the reply to the customer
# after a call that changed something. The note is built from the reply itself and says nothing
# about the task; the model's second reply is what the conversation gets. The note is not kept in
# the conversation.

HANDOVER_TOOL = "transfer_to_human_agents"
HANDOVER = "handover"
REQUESTS = "requests"
CHECK_HEADER = "Check by the system. This is not a message from the customer, and the customer does not see it."
HANDOVER_NOTE = (
    CHECK_HEADER + " You were about to transfer the customer to a human agent, with this summary: {held}\n"
    "A transfer ends your work on this conversation. Before it goes through, look once more at the policy and at "
    "your tools. If what the customer asked for can be done with your tools within the policy, do that instead and "
    "continue the conversation. If the policy requires the transfer, make the same transfer call again.")
REQUESTS_NOTE = (
    CHECK_HEADER + " You were about to send this reply: {held}\n"
    "Before it goes out, go through every request the customer has made in this conversation and check each one "
    "against the tool results above: done, refused under the policy, or still open. If a request is still open and "
    "the policy allows it, continue with it now (ask the customer for what you need, or make the call) instead of "
    "this reply. If every request is handled, send your reply.")


def write_tool_names(tools: list[Any]) -> set[str]:
    """The tools upstream marks as changing state."""
    return {tool.name for tool in tools if getattr(getattr(getattr(tool, "_func", None), "__tool_type__", None), "value", None) == "write"}


def check_note(items: list[dict[str, Any]], text: str, calls: list[dict[str, Any]], writes: set[str],
               usage: AgentUsage) -> tuple[str, str] | None:
    """Which check holds this reply, and its note; ``None`` when the reply goes through as it is."""
    for call in calls:
        if call["name"] == HANDOVER_TOOL:
            if HANDOVER in usage.checks:
                return None  # asked once already in this conversation: the transfer goes through
            return HANDOVER, HANDOVER_NOTE.format(held=json.dumps(call["arguments"].get("summary", ""), ensure_ascii=False))
    if calls or not text:
        return None
    written = sum(1 for item in items if item["role"] == "assistant" for call in item["calls"] if call["name"] in writes)
    if written <= usage.writes_checked:
        return None  # nothing was changed since the last check
    usage.writes_checked = written
    return REQUESTS, REQUESTS_NOTE.format(held=json.dumps(text, ensure_ascii=False))


# --- the hand-over rule (``--handover-rule``) -----------------------------------------------
#
# Off by default. With it, the transfer tool is not among the tools sent to the model until the
# customer has asked for a person, in the customer's own words. Until then the model can decline
# or carry on, but it cannot hand the conversation over. The rule reads the customer's messages
# and nothing else: no task, no expected action, no score.

ASKS_FOR_A_PERSON = re.compile(
    r"\b(human|representative|supervisor|manager|specialist|higher[- ]up|escalat\w*|"
    r"(a|an|another|real|live|actual) (person|agent)|(some|any)(one|body) (else|who|that)|have (some|any)(one|body)|"
    r"another (team|department)|different (agent|team|department|person)|"
    r"(connect|transfer|put|pass|hand) me\b|(speak|talk) (to|with) (some|any)(one|body))\b",
    re.IGNORECASE)
# "I don't want a supervisor" does not ask for one: a match that follows one of these, in the same sentence, is not counted.
DECLINES_A_PERSON = re.compile(r"\b(don'?t|do not|didn'?t|did not|no need|not asking|never|without|rather not|won'?t)\b[^.?!]{0,40}$", re.IGNORECASE)
# What the customer takes as being transferred: the policy's sentence, and other ways of saying it.
ANNOUNCES_TRANSFER = re.compile(
    r"\b(being transferred to|transferr(ed|ing) you|(transfer|connect|hand|pass|put)(ing)? you (now )?(to|with|over|off|through)|"
    r"(escalat(e|ed|ing)|forward(ed|ing)?) (this|your|you))\b", re.IGNORECASE)
# "I can't transfer you" announces nothing: a match that follows one of these, in the same sentence, is not counted.
DENIES_TRANSFER = re.compile(r"\b(can'?t|cannot|can not|unable|not able|won'?t|will not|don'?t|do not|no way|not possible|isn'?t|is not)\b[^.?!]{0,40}$",
                             re.IGNORECASE)
HANDOVER_REASKS = 2
HANDOVER_REFUSAL = (
    CHECK_HEADER + " A transfer to a human agent is not available at this point of the conversation: the customer has "
    "not asked for a person. Do not announce or promise a transfer. Tell the customer what you can and cannot do under "
    "the policy, and continue with what you can do.")


def customer_asked_for_a_person(items: list[dict[str, Any]]) -> bool:
    """Whether a message of the customer, so far, asks for a person (and does not say it wants none)."""
    for item in items:
        if item["role"] != "user":
            continue
        for match in ASKS_FOR_A_PERSON.finditer(item["text"]):
            if not DECLINES_A_PERSON.search(item["text"][:match.start()]):
                return True
    return False


def announces_handover(text: str, calls: list[dict[str, Any]]) -> bool:
    """Whether the reply hands the customer over: a call to the transfer tool, or words that say a transfer is happening."""
    if any(call["name"] == HANDOVER_TOOL for call in calls):
        return True
    text = text or ""
    return any(not DENIES_TRANSFER.search(text[:match.start()]) for match in ANNOUNCES_TRANSFER.finditer(text))


def policy_with_instruction(policy: str, instruction: str | None) -> str:
    """Upstream's policy; with ``--instructions``, the file's text after it, in the policy part."""
    return policy if instruction is None else f"{policy}\n\n{instruction}"


_registration = threading.Lock()


def register_agent() -> None:
    """Register ``BlaAgent`` in upstream's registry under ``AGENT_NAME`` (once); upstream then builds it as it builds its own."""
    with _registration:
        _register_agent()


def _register_agent() -> None:
    registry = load().registry
    if AGENT_NAME in registry._agent_factories:
        return
    agent_class = make_agent_class()

    def factory(tools: list[Any], domain_policy: str, **kwargs: Any) -> Any:
        attempt = _attempt.get()
        if attempt is None:
            raise RuntimeError("bla's agent is built only inside an attempt")
        return agent_class(tools, policy_with_instruction(domain_policy, attempt.instruction), provider=attempt.provider,
                           model=attempt.model, api_key=attempt.api_key, send=attempt.send, usage=attempt.usage,
                           finish_check=attempt.finish_check, handover_rule=attempt.handover_rule,
                           rules=attempt.rules)

    registry.register_agent_factory(factory, AGENT_NAME)


def make_agent_class() -> type:
    """``BlaAgent``, defined once upstream is importable (it subclasses upstream's ``LLMAgent``)."""
    load()
    import time

    from tau2.agent.llm_agent import LLMAgent
    from tau2.data_model.message import AssistantMessage, MultiToolMessage, ToolCall, UserMessage

    class BlaAgent(LLMAgent):
        """Upstream's ``LLMAgent`` whose model call is made by bla's provider code."""

        def __init__(self, tools: list[Any], domain_policy: str, *, provider: str, model: str, api_key: str,
                     send: Send, usage: AgentUsage, finish_check: bool = False, handover_rule: bool = False,
                     rules: tuple[str, ...] = ()):
            super().__init__(tools=tools, domain_policy=domain_policy, llm=model, llm_args=None)
            self.provider, self.model, self.api_key, self.send, self.usage = provider, model, api_key, send, usage
            self.finish_check, self.handover_rule, self.rules = finish_check, handover_rule, rules

        def _generate_next_message(self, message: Any, state: Any) -> Any:
            if isinstance(message, UserMessage) and message.is_audio:
                raise ValueError("User message cannot be audio. Use VoiceLLMAgent instead.")
            if isinstance(message, MultiToolMessage):
                state.messages.extend(message.tool_messages)
            else:
                state.messages.append(message)
            system = state.system_messages[0].content  # upstream keeps exactly one: the system prompt
            self.usage.messages = state.messages
            items = _messages(state.messages)
            # What the model is sent; the rules themselves read ``items``, the conversation as it is kept.
            shown = retail_rules.shown_items(items) if "products" in self.rules else items
            tools = tool_definitions(self.tools)
            withheld = False
            if self.handover_rule:
                if customer_asked_for_a_person(items):
                    self.usage.handover_offered = True
                else:
                    tools = [tool for tool in tools if tool["function"]["name"] != HANDOVER_TOOL]
                    withheld = True
            text, calls = self._ask(system, shown, tools)
            if withheld:
                for _ in range(HANDOVER_REASKS):
                    if not announces_handover(text, calls):
                        break
                    self.usage.handover_refusals += 1
                    text, calls = self._ask(system, [*shown, {"role": "user", "text": HANDOVER_REFUSAL}], tools)
                if any(call["name"] == HANDOVER_TOOL for call in calls):
                    raise AgentCallError("the model called the transfer tool, which was not among the tools it was sent")
                if announces_handover(text, calls):
                    self.usage.handover_announced += 1  # the customer will read a transfer that the tools never made
            if self.finish_check:
                held = check_note(items, text, calls, write_tool_names(self.tools), self.usage)
                if held is not None:
                    self.usage.checks.append(held[0])
                    text, calls = self._ask(system, [*shown, {"role": "user", "text": held[1]}], tools)
            if self.rules:
                text, calls = self._apply_rules(system, items, shown, tools, text, calls)
            return AssistantMessage(
                role="assistant", content=text or None,
                tool_calls=[ToolCall(id=c["id"], name=c["name"], arguments=c["arguments"]) for c in calls] or None)

        def _apply_rules(self, system: str, items: list[dict[str, Any]], shown: list[dict[str, Any]], tools: list[dict[str, Any]],
                         text: str, calls: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
            """``--rules``: at most one hold of this reply (each kind once in a conversation), then the address forms."""
            held: tuple[str, str] | None = None
            if ("handover-once" in self.rules and "handover-once" not in self.usage.rule_holds
                    and retail_rules.first_early_transfer(items, calls, customer_asked_for_a_person(items))):
                held = "handover-once", retail_rules.HANDOVER_ONCE_NOTE
                tools = [tool for tool in tools if tool["function"]["name"] != HANDOVER_TOOL]
            elif "payment" in self.rules and "payment" not in self.usage.rule_holds and retail_rules.payment_not_chosen(items, calls):
                held = "payment", retail_rules.payment_not_chosen(items, calls)
            elif "country" in self.rules and "country" not in self.usage.rule_holds and retail_rules.asks_for_country(text, calls):
                held = "country", retail_rules.COUNTRY_NOTE.format(held=json.dumps(text, ensure_ascii=False))
            if held is not None:
                self.usage.rule_holds.append(held[0])
                text, calls = self._ask(system, [*shown, {"role": "user", "text": held[1]}], tools)
                if held[0] == "handover-once" and any(call["name"] == HANDOVER_TOOL for call in calls):
                    raise AgentCallError("the model called the transfer tool, which was not among the tools it was sent")
            if "address" in self.rules:
                fixed = [retail_rules.fix_address(call) for call in calls]
                self.usage.address_corrections += sum(1 for before, after in zip(calls, fixed) if after is not before)
                calls = fixed
            return text, calls

        def _ask(self, system: str, items: list[dict[str, Any]], tools: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
            """One model call: its text and tool calls; its tokens are added to the attempt's usage."""
            started = time.perf_counter()
            if self.provider == "openai":
                reply = self.send("openai", self.api_key, openai_request(self.model, system, items, tools))
                parse = parse_openai
            else:
                try:
                    reply = self.send("anthropic", self.api_key, anthropic_request(self.model, system, items, tools))
                except Exception as error:
                    if FIRST_MESSAGE_ERROR not in str(error) or not items or items[0]["role"] != "assistant":
                        raise
                    # What litellm's Anthropic translation does under ``modify_params`` (a "." user turn first); without
                    # it upstream's own agent fails on every conversation, as the API wants a user turn first.
                    self.usage.opening_turn_added = True
                    reply = self.send("anthropic", self.api_key, anthropic_request(self.model, system, items, tools, opening=True))
                parse = parse_anthropic
            try:
                text, calls, call = parse(reply)
            except AgentCallError:
                # A reply that was refused or cut off still cost tokens: keep them.
                try:
                    self._note_unparsed(reply)
                except Exception:
                    pass
                raise
            call.latency_seconds = time.perf_counter() - started
            self.usage.calls.append(call)
            return text, calls

        def _note_unparsed(self, reply: dict[str, Any]) -> None:
            usage = reply.get("usage") or {}
            if self.provider == "openai":
                cached = _int((usage.get("input_tokens_details") or {}).get("cached_tokens"))
                call = AgentCall(reply.get("model"), max(_int(usage.get("input_tokens")) - cached, 0), 0, cached,
                                 _int(usage.get("output_tokens")), reply.get("status"), usage_reported=_complete(usage))
            else:
                call = AgentCall(reply.get("model"), _int(usage.get("input_tokens")), _int(usage.get("cache_creation_input_tokens")),
                                 _int(usage.get("cache_read_input_tokens")), _int(usage.get("output_tokens")), reply.get("stop_reason"),
                                 usage_reported=_complete(usage))
            self.usage.calls.append(call)

    return BlaAgent
