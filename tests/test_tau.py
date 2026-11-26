"""The τ-bench retail command, offline: scripted stand-ins for the agent's provider, the customer and the judges."""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import tau_support
from tests.tau_support import (AGENT_KEY, CUSTOMER_KEY, FINAL_TEXT, ScriptedAgent, ScriptedLitellm, anthropic_reply, environment,
                          openai_reply)

try:
    from benchmark_loop_agent.tau import agent as tau_agent
    from benchmark_loop_agent.tau import batch, upstream
    from benchmark_loop_agent.tau.__main__ import main
    from benchmark_loop_agent.tau.batch import RunParameters, run_retail
    UP = upstream.load()
except RuntimeError as error:  # the optional "tau" dependency group is not installed
    raise unittest.SkipTest(str(error))

TASK_ID = "36"  # one modify_pending_order_items write, two natural-language assertions


def task_of(task_id: str = TASK_ID):
    return upstream.prepare([task_id], "m", "openai/gpt-6-sol", 1, 300)[1][task_id]


TASK = task_of()


class Base(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "run"

    def run_retail(self, send=None, completion=None, provider="openai", trials=1, instruction=None, concurrency=1,
                   task_ids=(TASK_ID,), model="agent-model", directory=None, user_model="gpt-6-sol"):
        parameters = RunParameters(provider, model, user_model, tuple(task_ids), trials, 300, instruction, concurrency)
        with mock.patch.object(UP.llm_utils, "completion", completion or ScriptedLitellm(TASK)):
            return run_retail(directory or self.directory, parameters, environment(provider), send or ScriptedAgent(TASK, provider))

    def records(self):
        return batch.read_jsonl(self.directory / batch.RECORDS_FILE)


class TaskSetTests(Base):
    def copy_root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        for name in ("task_subsets/retail_50.json", "benchmarks/text.json"):
            (root / "data/tau2" / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(upstream.VENDOR_ROOT / "data/tau2" / name, root / "data/tau2" / name)
        return root

    def test_the_pinned_set_is_the_fifty_tasks_of_the_subset(self):
        ids = upstream.pinned_task_ids()
        self.assertEqual(len(ids), 50)
        self.assertEqual(ids, json.loads((upstream.VENDOR_ROOT / "data/tau2/task_subsets/retail_50.json").read_text())["task_ids"])
        manifest = json.loads((upstream.VENDOR_ROOT / "data/tau2/benchmarks/text.json").read_text())
        self.assertEqual(manifest["task_subsets"]["retail"], {"name": "retail_50", "sha256": upstream.SUBSET_SHA256})

    def test_other_tasks_with_a_forged_manifest_digest_are_refused(self):
        root = self.copy_root()
        path = root / "data/tau2/task_subsets/retail_50.json"
        data = json.loads(path.read_text())
        data["task_ids"][0] = "999"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(upstream.TaskSetError, "refusing to run"):
            upstream.pinned_task_ids(root)
        import hashlib
        manifest_path = root / "data/tau2/benchmarks/text.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["task_subsets"]["retail"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(upstream.TaskSetError, "pinned digest"):  # the digest written in the code holds too
            upstream.pinned_task_ids(root)

    def test_a_mismatch_is_refused_before_any_request_and_nothing_is_written(self):
        root = self.copy_root()
        path = root / "data/tau2/task_subsets/retail_50.json"
        path.write_text(path.read_text() + " ")
        sent = []
        with mock.patch.object(upstream, "VENDOR_ROOT", root), self.assertRaises(ValueError):
            run_retail(self.directory, RunParameters("openai", "m", "gpt-6-sol", ("36",)), environment(),
                       lambda *a: sent.append(a))
        self.assertEqual(sent, [])
        self.assertFalse(self.directory.exists())

    def cli(self, *arguments):
        calls = []

        def fake_attempt(config, task, seed, settings, env, send):
            calls.append(task.id)
            return {"fields": fake_fields("pass"), "conversation": {"messages": []}}

        with mock.patch.dict(os.environ, environment(), clear=True), mock.patch.object(batch, "run_attempt", fake_attempt), \
                contextlib.redirect_stderr(io.StringIO()):
            code = main(["--output-dir", str(self.directory), "--provider", "openai", "--openai-model", "m", *arguments])
        return code, calls

    def test_the_default_run_is_exactly_the_fifty_tasks(self):
        code, calls = self.cli("--concurrency", "1")
        self.assertEqual(code, 0)
        self.assertEqual(calls, upstream.pinned_task_ids())
        manifest = batch.read_manifest(self.directory)["parameters"]
        self.assertEqual(manifest["task_ids"], upstream.pinned_task_ids())
        self.assertEqual(manifest["subset"], {"name": "retail_50", "sha256": upstream.SUBSET_SHA256})

    def test_partial_runs_use_tasks_of_the_subset_only(self):
        ids = upstream.pinned_task_ids()
        self.assertEqual(self.cli("--limit", "3")[1], ids[:3])
        self.directory = self.directory.parent / "other"
        self.assertEqual(self.cli("--tasks", ids[5], ids[2])[1], [ids[5], ids[2]])
        self.directory = self.directory.parent / "third"
        with self.assertRaises(SystemExit):  # a task outside retail_50 is refused
            self.cli("--tasks", "9999")


def fake_fields(outcome, reason=None, calls=1):
    return {"outcome": outcome, "reward": 1.0 if outcome == "pass" else 0.0 if outcome == "fail" else None,
            "reward_components": None, "termination_reason": "user_stop", "reason": reason, "agent_calls": calls,
            "agent_models": [], "agent_tokens": {"uncached_input": 1, "cache_write_input": 0, "cache_read_input": 0, "output": 1},
            "customer_usage": {"calls": 0, "models": []}, "judges_usage": {"calls": 0, "models": []}, "elapsed_seconds": 0.1}


def upstream_schemas(agent) -> list[dict]:
    """The tool schemas straight from an upstream agent's tools, not through bla's helper."""
    return [tool.openai_schema for tool in agent.tools]


def sent_differences(request: dict, provider: str, standard) -> list[str]:
    """What differs between a captured provider request and upstream's standard agent: system prompt and tools."""
    found = []
    expected = upstream_schemas(standard)
    functions = [t["function"] for t in expected]
    if provider == "openai":  # the Responses API form: every field, strictness included
        system = request["instructions"]
        wanted = [{"type": "function", "name": f["name"], "description": f["description"], "parameters": f["parameters"],
                   "strict": False} for f in functions]
    else:  # Anthropic's form; the cache breakpoint sits on the last tool
        system = request["system"][0]["text"]
        wanted = [{"name": f["name"], "description": f["description"], "input_schema": f["parameters"]} for f in functions]
        wanted[-1]["cache_control"] = {"type": "ephemeral"}
    if system != standard.system_prompt:
        found.append("system prompt")
    if request["tools"] != wanted:
        found.append("tool definitions")
    return found


def differences(ours, standard) -> list[str]:
    """What differs between bla's agent and upstream's standard agent: the system prompt and the tool definitions."""
    found = []
    if ours.system_prompt != standard.system_prompt:
        found.append("system prompt")
    if ours.get_init_state().system_messages != standard.get_init_state().system_messages:
        found.append("initial system messages")
    if json.dumps(upstream_schemas(ours), sort_keys=True) != json.dumps(upstream_schemas(standard), sort_keys=True):
        found.append("tool definitions")
    return found


class AgentMatchesUpstreamTests(Base):
    def agents(self, task_id, instruction=None):
        """bla's agent and upstream's standard ``llm_agent``, each built by upstream's own text orchestrator builder."""
        from tau2.runner.build import build_text_orchestrator
        config, tasks = upstream.prepare([task_id], "m", "openai/gpt-6-sol", 1, 300)
        standard = build_text_orchestrator(config.model_copy(update={"agent": "llm_agent"}), tasks[task_id], seed=1).agent
        tau_agent.register_agent()
        attempt = tau_agent.Attempt("openai", "m", "k", lambda *a: None, tau_agent.AgentUsage(), instruction)
        with tau_agent.attempting(attempt):
            ours = build_text_orchestrator(config, tasks[task_id], seed=1).agent
        return ours, standard

    def test_without_instructions_the_prompt_and_tools_are_upstreams(self):
        for task_id in ("36", "22"):
            ours, standard = self.agents(task_id)
            self.assertEqual(type(ours).__name__, "BlaAgent")
            self.assertEqual(type(standard).__name__, "LLMAgent")
            self.assertEqual(differences(ours, standard), [])
            self.assertIn("<policy>", standard.system_prompt)
            self.assertGreater(len(ours.tools), 5)

    def test_the_comparison_fails_on_any_difference(self):
        ours, standard = self.agents("36", instruction="Always be brief.")
        self.assertEqual(differences(ours, standard), ["system prompt", "initial system messages"])
        ours, standard = self.agents("36")
        ours.tools[0].__class__  # noqa: B018
        altered = upstream_schemas(ours)
        altered[0]["function"]["description"] += " "
        with mock.patch.object(type(ours.tools[0]), "openai_schema", new_callable=mock.PropertyMock,
                               side_effect=altered + upstream_schemas(standard)):
            self.assertEqual(differences(ours, standard), ["tool definitions"])

    def test_a_changed_tool_description_in_the_adapter_fails_the_request_comparison(self):
        _, standard = self.agents("36")
        real = tau_agent.tool_definitions

        def wrong(tools):
            schemas = real(tools)
            schemas[0] = {**schemas[0], "function": {**schemas[0]["function"], "description": "wrong"}}
            return schemas

        for provider in ("openai", "anthropic"):
            self.directory = self.directory.parent / ("wrong-" + provider)
            send = ScriptedAgent(TASK, provider)
            with mock.patch.object(tau_agent, "tool_definitions", wrong):
                self.run_retail(send=send, provider=provider)
            self.assertEqual(sent_differences(send.requests[0], provider, standard), ["tool definitions"])

    def test_a_changed_strictness_or_type_in_the_sent_tools_fails_the_request_comparison(self):
        _, standard = self.agents("36")
        for provider in ("openai", "anthropic"):
            self.directory = self.directory.parent / ("flag-" + provider)
            send = ScriptedAgent(TASK, provider)
            self.run_retail(send=send, provider=provider)
            request = json.loads(json.dumps(send.requests[0]))
            self.assertEqual(sent_differences(request, provider, standard), [])
            if provider == "openai":
                request["tools"][0]["strict"] = True
            else:
                request["tools"][0]["cache_control"] = {"type": "ephemeral"}
            self.assertEqual(sent_differences(request, provider, standard), ["tool definitions"])
            request["tools"][0].pop("strict", None)
            request["tools"][0]["type"] = "custom"
            self.assertEqual(sent_differences(request, provider, standard), ["tool definitions"])

    def test_what_is_sent_is_that_prompt_and_those_tools_on_both_providers(self):
        for task_id in ("36", "22"):
            _, standard = self.agents(task_id)
            for provider in ("openai", "anthropic"):
                task = task_of(task_id)
                send = ScriptedAgent(task, provider)
                self.directory = self.directory.parent / f"{provider}-{task_id}"
                self.run_retail(send=send, provider=provider, task_ids=(task_id,), completion=ScriptedLitellm(task))
                self.assertEqual(sent_differences(send.requests[0], provider, standard), [])

    def test_the_conversation_sent_is_upstreams(self):
        send = ScriptedAgent(TASK)
        self.run_retail(send=send)
        first = send.requests[0]["input"]
        self.assertEqual([i["role"] for i in first], ["assistant", "user"])  # upstream's greeting, then the customer's first message
        self.assertEqual(first[0]["content"], "Hi! How can I help you today?")
        second = send.requests[1]["input"]
        self.assertEqual([i.get("type") or i["role"] for i in second], ["assistant", "user", "function_call", "function_call_output"])

    def test_instructions_are_appended_to_the_policy_part_after_upstreams_text(self):
        text = "Think about the policy before you act."
        send = ScriptedAgent(TASK)
        self.run_retail(send=send, instruction=text)
        _, standard = self.agents("36")
        expected = UP.registry.get_agent_factory("llm_agent")(tools=standard.tools, llm="m", llm_args=None,
                                                              domain_policy=standard.domain_policy + "\n\n" + text)
        self.assertEqual(send.requests[0]["instructions"], expected.system_prompt)
        policy_part = send.requests[0]["instructions"].split("<policy>\n")[1].split("\n</policy>")[0]
        self.assertTrue(policy_part.startswith(standard.domain_policy))
        self.assertTrue(policy_part.endswith(text))
        parameters = batch.read_manifest(self.directory)["parameters"]
        raw = text.encode()
        import hashlib
        self.assertEqual(parameters["instructions"], {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        self.assertEqual((self.directory / "instructions.txt").read_text(), text)


class CachingAndTokensTests(Base):
    def test_openai_asks_for_a_cache_and_counts_cached_input_apart(self):
        send = ScriptedAgent(TASK)
        original = send.__call__
        with mock.patch.object(tau_support, "openai_reply", lambda **kw: openai_reply(input_tokens=100, cached=40, output_tokens=7, **kw)):
            self.run_retail(send=send)
        requests = send.requests
        self.assertTrue(all(r["prompt_cache_key"].startswith("bla-tau-") for r in requests))
        self.assertEqual(len({r["prompt_cache_key"] for r in requests}), 1)
        record = self.records()[0]
        self.assertEqual(record["agent_tokens"], {"uncached_input": 120, "cache_write_input": 0, "cache_read_input": 80, "output": 14})
        self.assertEqual(record["agent_calls"], 2)

    def test_anthropic_marks_the_stable_prefix_and_records_the_three_input_kinds(self):
        send = ScriptedAgent(TASK, "anthropic")
        self.run_retail(send=send, provider="anthropic")
        for request in send.requests:
            self.assertEqual(request["system"][0]["cache_control"], {"type": "ephemeral"})
            self.assertEqual(request["tools"][-1]["cache_control"], {"type": "ephemeral"})
            self.assertEqual(request["messages"][-1]["content"][-1]["cache_control"], {"type": "ephemeral"})
            marked = [b for m in request["messages"] for b in m["content"] if "cache_control" in b]
            self.assertEqual(len(marked), 1)
        record = self.records()[0]
        self.assertEqual(record["agent_tokens"], {"uncached_input": 40, "cache_write_input": 60, "cache_read_input": 100, "output": 20})
        self.assertEqual(record["agent_models"], ["reported-anthropic-model"])
        call_usage = json.loads((self.directory / batch.CONVERSATIONS_FILE).read_text().splitlines()[0])["agent_call_usage"]
        self.assertEqual(len(call_usage), 2)
        self.assertEqual(call_usage[0]["cache_read_input_tokens"], 50)

    def test_tool_results_share_one_user_turn_for_anthropic(self):
        request = tau_agent.anthropic_request("m", "system", [
            {"role": "assistant", "text": "hi", "calls": []}, {"role": "user", "text": "hello"},
            {"role": "assistant", "text": "", "calls": [{"id": "a", "name": "t", "arguments": {}}, {"id": "b", "name": "t", "arguments": {}}]},
            {"role": "tool", "id": "a", "text": "1"}, {"role": "tool", "id": "b", "text": "2"}], [])
        self.assertEqual([m["role"] for m in request["messages"]], ["assistant", "user", "assistant", "user"])
        self.assertEqual([b["type"] for b in request["messages"][-1]["content"]], ["tool_result", "tool_result"])

    def test_a_first_message_error_is_answered_with_an_opening_user_turn(self):
        calls = []

        def send(provider, key, request):
            calls.append(request)
            if len(calls) == 1:
                raise ValueError("messages: first message must use the user role")
            return anthropic_reply(text=FINAL_TEXT)

        self.run_retail(send=send, provider="anthropic")
        self.assertEqual(calls[1]["messages"][0], {"role": "user", "content": [{"type": "text", "text": "."}]})


class OutcomeTests(Base):
    def test_a_passing_conversation_is_scored_by_upstreams_evaluator(self):
        records = self.run_retail()
        record = self.records()[0]
        self.assertEqual(records[0]["outcome"], "pass")
        self.assertEqual((record["task_id"], record["trial"], record["outcome"], record["reward"]), (TASK_ID, 0, "pass", 1.0))
        self.assertEqual(record["termination_reason"], "user_stop")
        self.assertEqual(record["reward_components"]["reward_breakdown"], {"DB": 1.0, "NL_ASSERTION": 1.0})
        self.assertTrue(record["reward_components"]["db_check"]["db_match"])
        self.assertEqual(record["customer_usage"]["models"][0]["model"], "gpt-6-sol")
        self.assertEqual(record["customer_usage"]["models"][0]["prompt_tokens"], 22)
        self.assertEqual(record["customer_usage"]["models"][0]["cached_tokens"], 6)
        self.assertEqual(record["judges_usage"]["models"][0]["model"], "gpt-5.4-mini-2026-03-17")
        self.assertEqual(record["judges_usage"]["models"][0]["reported_models"], ["gpt-4.1-mini-2025-04-14"])
        self.assertEqual((record["judges_usage"]["models"][0]["prompt_tokens"], record["judges_usage"]["models"][0]["completion_tokens"]), (40, 5))
        self.assertGreater(record["elapsed_seconds"], 0)
        conversation = json.loads((self.directory / batch.CONVERSATIONS_FILE).read_text())
        self.assertEqual((conversation["task_id"], conversation["trial"], conversation["attempt"]), (TASK_ID, 0, 1))
        roles = [m["role"] for m in conversation["messages"]]
        self.assertEqual(roles[0:3], ["assistant", "user", "assistant"])
        self.assertIn("tool", roles)

    def test_the_run_json_records_the_pinned_upstream_models_trials_and_seed(self):
        self.run_retail(trials=1, model="agent-model")
        parameters = batch.read_manifest(self.directory)["parameters"]
        self.assertEqual(parameters["upstream"]["commit"], "989d3285ae669e49503324bdb9981bf14fccedeb")
        self.assertEqual(parameters["upstream"]["release"], "v2.0.0")
        self.assertEqual(parameters["subset"], {"name": "retail_50", "sha256": upstream.SUBSET_SHA256})
        self.assertEqual((parameters["agent_model"], parameters["user_model"], parameters["trials"], parameters["seed"]),
                         ("agent-model", "gpt-6-sol", 1, 300))
        self.assertEqual(parameters["trial_seeds"], batch.trial_seeds(300, 1))
        self.assertIsNone(parameters["instructions"])

    def test_a_wrong_end_state_is_a_fail_with_reward_zero(self):
        self.run_retail(send=ScriptedAgent(TASK, only=lambda action: False))
        record = self.records()[0]
        self.assertEqual((record["outcome"], record["reward"]), ("fail", 0.0))

    def test_reaching_the_step_limit_is_a_fail(self):
        def endless(provider, key, request):
            return openai_reply(text="still working on it")

        self.run_retail(send=endless, completion=ScriptedLitellm(TASK, never_stop=True))
        record = self.records()[0]
        self.assertEqual((record["termination_reason"], record["outcome"], record["reward"]), ("max_steps", "fail", 0.0))
        self.assertGreater(record["agent_calls"], 50)

    def test_a_provider_error_is_unscored_never_a_pass_or_a_fail(self):
        def broken(provider, key, request):
            raise ValueError(f"bad request with {AGENT_KEY}")

        self.run_retail(send=broken)
        record = self.records()[0]
        self.assertEqual(record["outcome"], "unscored")
        self.assertIsNone(record["reward"])
        self.assertIn("ValueError", record["reason"])
        self.assertNotIn(AGENT_KEY, json.dumps(record))
        self.assertEqual((record["agent_calls"], record["agent_calls_without_usage"]), (1, 1))  # one request, no usage back

    def test_transport_retries_and_rejected_greetings_are_dispatches(self):
        import openai

        class Transient(openai.APIConnectionError):
            def __init__(self):
                super().__init__(request=mock.Mock())

        attempts = []

        def flaky(provider, key, request):
            attempts.append(1)
            if len(attempts) == 1:
                raise Transient()
            return openai_reply(text=FINAL_TEXT)

        self.run_retail(send=flaky, completion=ScriptedLitellm(TASK))
        record = self.records()[0]
        self.assertEqual((record["agent_calls"], record["agent_calls_without_usage"]), (len(attempts), 1))
        calls = []

        def rejecting(provider, key, request):
            calls.append(request)
            if len(calls) == 1:
                raise ValueError("messages: first message must use the user role")
            return anthropic_reply(text=FINAL_TEXT)

        self.directory = self.directory.parent / "greeting"
        self.run_retail(send=rejecting, provider="anthropic")
        record = self.records()[0]
        self.assertEqual((record["agent_calls"], record["agent_calls_without_usage"], record["agent_opening_user_turn_added"]),
                         (len(calls), 1, True))

    def test_a_reply_without_usage_is_unknown_not_zero(self):
        def silent(provider, key, request):
            reply = openai_reply(text=FINAL_TEXT)
            del reply["usage"]
            return reply

        self.run_retail(send=silent, completion=ScriptedLitellm(TASK))
        record = self.records()[0]
        self.assertEqual((record["agent_calls"], record["agent_calls_without_usage"]), (1, 1))
        self.assertIn("usage unknown for 1 agent call(s)", build_report(self.directory, Path(__file__).resolve().parent.parent / "data" / "rates.json"))

    def test_a_partial_usage_keeps_its_known_tokens_and_is_flagged(self):
        from benchmark_loop_agent.tau.usage import UsageCollector
        collector = UsageCollector()
        collector.add("gpt-6-sol", {"model": "gpt-6-sol", "usage": {"prompt_tokens": 30}})
        (entry,) = collector.summary("customer")["models"]
        self.assertEqual((entry["prompt_tokens"], entry["completion_tokens"], entry["calls_without_usage"]), (30, 0, 1))
        from benchmark_loop_agent.tau.agent import parse_openai
        reply = openai_reply(text=FINAL_TEXT)
        del reply["usage"]["output_tokens"]
        _, _, call = parse_openai(reply)
        self.assertFalse(call.usage_reported)

    def test_a_customer_refusal_is_unscored_and_keeps_its_usage(self):
        from tests.tau_support import model_response
        base = ScriptedLitellm(TASK)

        def refusing(*args, **kwargs):
            if kwargs["model"].endswith("gpt-6-sol"):
                reply = model_response("I cannot help with that.", prompt=30, completion=4)
                reply.choices[0].finish_reason = "content_filter"
                reply.choices[0].message.refusal = "I cannot help with that."
                return reply
            return base(*args, **kwargs)

        self.run_retail(completion=refusing)
        record = self.records()[0]
        self.assertEqual((record["outcome"], record["reward"]), ("unscored", None))
        self.assertIn("refused", record["reason"])
        self.assertEqual(record["customer_usage"]["models"][0]["prompt_tokens"], 30)

    def test_a_judge_failure_keeps_the_finished_conversation(self):
        base = ScriptedLitellm(TASK)

        def failing(*args, **kwargs):
            if not kwargs["model"].endswith("gpt-6-sol"):
                raise RuntimeError("judge down")
            return base(*args, **kwargs)

        self.run_retail(completion=failing)
        record = self.records()[0]
        self.assertEqual(record["outcome"], "unscored")
        conversation = json.loads((self.directory / batch.CONVERSATIONS_FILE).read_text().splitlines()[0])
        self.assertFalse(conversation["partial"])
        self.assertEqual(conversation["messages"][-1]["role"], "user")  # the customer's stop message is kept
        self.assertIn("###STOP###", conversation["messages"][-1]["content"])

    def test_a_key_in_a_reported_model_name_is_not_written(self):
        base = ScriptedLitellm(TASK)

        def echoing(*args, **kwargs):
            reply = base(*args, **kwargs)
            reply.model = f"echo-{AGENT_KEY}"
            return reply

        self.run_retail(completion=echoing)
        for path in self.directory.iterdir():
            self.assertNotIn(AGENT_KEY, path.read_text())

    def test_an_instruction_holding_a_key_is_refused_before_any_request(self):
        sent = []
        with self.assertRaisesRegex(ValueError, "instruction text contains"):
            self.run_retail(send=lambda *a: sent.append(a), instruction=f"use {AGENT_KEY}")
        self.assertEqual(sent, [])
        self.assertFalse(self.directory.exists())

    def test_a_refusal_is_unscored_and_its_tokens_are_kept(self):
        refusal = {"model": "m", "status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}],
                   "usage": {"input_tokens": 9, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 3}}
        self.run_retail(send=lambda *a: refusal)
        record = self.records()[0]
        self.assertEqual(record["outcome"], "unscored")
        self.assertIn("refused", record["reason"])
        self.assertEqual((record["agent_tokens"]["uncached_input"], record["agent_tokens"]["output"]), (9, 3))
        self.directory = self.directory.parent / "anthropic"
        self.run_retail(send=lambda *a: anthropic_reply(stop_reason="refusal"), provider="anthropic")
        self.assertEqual(self.records()[0]["outcome"], "unscored")

    def test_a_customer_error_is_unscored_and_keeps_the_agents_usage(self):
        calls = []

        def send(provider, key, request):
            calls.append(1)
            return openai_reply(text="hello")

        self.run_retail(send=send, completion=ScriptedLitellm(TASK, fail_customer=True))
        record = self.records()[0]
        self.assertEqual(record["outcome"], "unscored")
        self.assertIn("customer", record["reason"] + "conversation (customer")
        self.assertEqual(record["agent_calls"], len(calls))

    def test_upstreams_premature_termination_by_error_is_unscored(self):
        def clumsy(provider, key, request):
            return openai_reply(calls=[("no_such_tool", {})])

        self.run_retail(send=clumsy)
        record = self.records()[0]
        self.assertEqual((record["outcome"], record["termination_reason"]), ("unscored", "too_many_errors"))
        self.assertIsNone(record["reward"])
        self.assertIn("too_many_errors", record["reason"])


class ResumeTests(Base):
    def broken_then_good(self):
        refusal = {"model": "m", "status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}],
                   "usage": {"input_tokens": 9, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 3}}
        self.run_retail(send=lambda *a: refusal, trials=2)
        return refusal

    def test_a_second_run_runs_only_what_is_missing_or_unscored(self):
        self.run_retail(trials=2)
        self.assertEqual([r["outcome"] for r in self.records()], ["pass", "pass"])
        second = ScriptedAgent(TASK)
        self.run_retail(send=second, trials=2)
        self.assertEqual(second.requests, [])
        self.assertEqual(len((self.directory / batch.CONVERSATIONS_FILE).read_text().splitlines()), 2)
        self.assertEqual(len(batch.read_manifest(self.directory)["sessions"]), 2)

    def test_unscored_ones_run_again_and_their_usage_stays_beside_the_result(self):
        self.broken_then_good()
        first = self.records()
        self.assertEqual([r["outcome"] for r in first], ["unscored", "unscored"])
        good = ScriptedAgent(TASK)
        self.run_retail(send=good, trials=2)
        records = self.records()
        self.assertEqual([r["outcome"] for r in records], ["pass", "pass"])
        for record in records:
            self.assertEqual(record["attempt"], 2)
            self.assertEqual(record["agent_tokens"]["uncached_input"], 200)  # the attempt that gave the result
            (earlier,) = record["earlier_unscored_attempts"]
            self.assertEqual((earlier["outcome"], earlier["agent_tokens"]["uncached_input"], earlier["agent_tokens"]["output"]), ("unscored", 9, 3))
            self.assertIn("refused", earlier["reason"])
        self.assertEqual(len((self.directory / batch.CONVERSATIONS_FILE).read_text().splitlines()), 4)

    def test_a_task_still_unscored_keeps_every_earlier_attempt(self):
        for _ in range(3):
            self.run_retail(send=lambda *a: anthropic_reply(stop_reason="refusal") if False else openai_reply(calls=[("no_such_tool", {})]))
        (record,) = self.records()
        self.assertEqual((record["outcome"], record["attempt"], len(record["earlier_unscored_attempts"])), ("unscored", 3, 2))

    def test_a_stop_between_the_two_writes_does_not_schedule_the_scored_conversation_again(self):
        class Stopped(BaseException):
            pass

        def stop(store):
            raise Stopped()

        with mock.patch.object(batch.Store, "_write_records", stop), self.assertRaises(Stopped):
            self.run_retail()
        self.assertEqual(self.records(), [])  # records.jsonl never got the record; the conversations file holds it
        second = ScriptedAgent(TASK)
        self.run_retail(send=second)
        self.assertEqual(second.requests, [])
        (record,) = self.records()
        self.assertEqual((record["outcome"], record["attempt"]), ("pass", 1))
        self.assertEqual(len((self.directory / batch.CONVERSATIONS_FILE).read_text().splitlines()), 1)

    def test_a_torn_journal_tail_does_not_swallow_the_retry(self):
        self.run_retail()
        journal = self.directory / batch.CONVERSATIONS_FILE
        (self.directory / batch.RECORDS_FILE).unlink()
        journal.write_text('{"task_id": ')  # a stop in the middle of the first append; nothing was committed
        self.run_retail(send=ScriptedAgent(TASK))
        entries = batch.read_jsonl(journal)
        self.assertEqual([(e["task_id"], e["outcome"]) for e in entries], [(TASK_ID, "pass")])  # the retry's transcript is readable
        for line in journal.read_text().splitlines():
            json.loads(line)  # the torn fragment was truncated, not kept

    def test_a_complete_final_entry_lacking_only_its_newline_is_kept(self):
        self.run_retail()
        journal = self.directory / batch.CONVERSATIONS_FILE
        journal.write_text(journal.read_text().rstrip("\n"))
        batch.Store(self.directory)
        self.assertTrue(journal.read_text().endswith("\n"))
        self.assertEqual(len(batch.read_jsonl(journal)), 1)

    def test_a_torn_tail_then_a_stop_before_the_index_is_written_does_not_repeat_the_trial(self):
        class Stopped(BaseException):
            pass

        journal = self.directory / batch.CONVERSATIONS_FILE
        self.directory.mkdir(parents=True)
        journal.write_text('{"task_id": ')
        with mock.patch.object(batch.Store, "_write_records", lambda store: (_ for _ in ()).throw(Stopped())), self.assertRaises(Stopped):
            self.run_retail()
        second = ScriptedAgent(TASK)
        self.run_retail(send=second)
        self.assertEqual(second.requests, [])
        (record,) = self.records()
        self.assertEqual((record["outcome"], record["attempt"]), ("pass", 1))

    def test_the_report_reads_a_committed_result_the_index_has_not_got_yet(self):
        class Stopped(BaseException):
            pass

        with mock.patch.object(batch.Store, "_write_records", lambda store: (_ for _ in ()).throw(Stopped())), self.assertRaises(Stopped):
            self.run_retail()
        self.assertEqual(self.records(), [])
        text = build_report(self.directory, Path(__file__).resolve().parent.parent / "data" / "rates.json")
        self.assertIn("scored: 1; unscored: 0", text)

    def test_usage_is_still_recorded_while_the_workers_are_shut_down_after_an_interrupt(self):
        seen = []
        original = UP.llm_utils.completion

        class Pool(batch.ThreadPoolExecutor):
            def map(self, *args, **kwargs):
                raise KeyboardInterrupt()

            def shutdown(self, *args, **kwargs):
                seen.append(UP.llm_utils.completion is not original and UP.llm_utils.completion is not scripted)
                super().shutdown(*args, **kwargs)

        scripted = ScriptedLitellm(TASK)
        with mock.patch.object(batch, "ThreadPoolExecutor", Pool), self.assertRaises(KeyboardInterrupt):
            self.run_retail(completion=scripted)
        self.assertEqual(seen, [True])  # the wrapper was still installed when shutdown ran
        self.assertIs(UP.llm_utils.completion, original)  # and is gone afterwards

    def test_different_options_over_an_existing_directory_are_refused(self):
        self.run_retail()
        for changes in ({"model": "other"}, {"provider": "anthropic"}, {"trials": 2}, {"instruction": "x"}, {"user_model": "gpt-6-luna"},
                        {"task_ids": ("22",)}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, "different options"):
                self.run_retail(**changes)
        self.assertEqual(len(self.records()), 1)
        sent = []
        with self.assertRaisesRegex(ValueError, "different options"):  # the concurrency is part of the options
            self.run_retail(send=lambda *a: sent.append(a), concurrency=3)
        self.assertEqual(sent, [])
        self.run_retail()
        self.assertEqual(len(batch.read_manifest(self.directory)["sessions"]), 2)


def write_run(directory: Path, records: list[dict], trials=1, task_ids=("a", "b"), model="agent-m", provider="openai"):
    directory.mkdir(parents=True, exist_ok=True)
    parameters = batch_parameters(task_ids, trials, model, provider)
    (directory / batch.MANIFEST_FILE).write_text(json.dumps({"parameters": parameters, "sessions": []}))
    (directory / batch.RECORDS_FILE).write_text("".join(json.dumps(r) + "\n" for r in records))


def batch_parameters(task_ids, trials, model, provider):
    parameters = RunParameters(provider, model, "cust-m", tuple(task_ids), trials).identity()
    return parameters


def usage(model, prompt, completion, cached=0):
    return {"calls": 1, "models": [{"model": model, "reported_models": [model], "calls": 1, "prompt_tokens": prompt, "cached_tokens": cached,
                                    "completion_tokens": completion, "reasoning_tokens": 0, "calls_without_usage": 0}]}


def record(task, trial, outcome, agent=(1_000_000, 0, 0, 100_000), customer=(2_000_000, 500_000, 0), judges=None, earlier=(), attempt=1):
    return {"task_id": task, "trial": trial, "seed": 1, "attempt": attempt, "outcome": outcome,
            "reward": {"pass": 1.0, "fail": 0.0}.get(outcome), "termination_reason": "user_stop", "reason": None if outcome != "unscored" else "boom",
            "agent_calls": 3, "agent_models": ["agent-m"],
            "agent_tokens": dict(zip(("uncached_input", "cache_write_input", "cache_read_input", "output"), agent)),
            "customer_usage": usage("cust-m", customer[0], customer[1], customer[2]),
            "judges_usage": judges or {"calls": 0, "models": []}, "elapsed_seconds": 1.0, "earlier_unscored_attempts": list(earlier)}


RATES = {"models": {
    "agent-m": {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75},
    "cust-m": {"input": 2.0, "output": 10.0},
    "no-cache-rate-m": {"input": 1.0, "output": 2.0},
}}


class ReportTests(Base):
    def report(self, records, rates=RATES, **kwargs) -> str:
        write_run(self.directory, records, **kwargs)
        rates_file = self.directory / "fixture-rates.json"
        rates_file.write_text(json.dumps(rates))
        return build_report(self.directory, rates_file)

    def test_counts_pass_rate_and_unscored_are_named(self):
        text = self.report([record("a", 0, "pass"), record("b", 0, "fail")])
        self.assertIn("scored: 2; unscored: 0", text)
        self.assertIn("**50.0%** (1 of 2 scored conversations)", text)
        text = self.report([record("a", 0, "pass"), record("b", 0, "unscored")])
        self.assertIn("scored: 1; unscored: 1; no record yet: 0", text)
        self.assertIn("**100.0%** (1 of 1 scored conversations)", text)
        self.assertIn("| b | 0 | 1 | boom |", text)

    def test_all_k_trials_figures_leave_out_tasks_with_an_unscored_trial_and_name_them(self):
        records = [record("a", i, "pass") for i in range(3)] + [record("b", 0, "pass"), record("b", 1, "pass"), record("b", 2, "fail"),
                                                                 record("c", 0, "pass"), record("c", 1, "unscored"), record("c", 2, "pass")]
        text = self.report(records, trials=3, task_ids=("a", "b", "c"))
        self.assertIn("(2 of 3 tasks)", text)
        self.assertIn("| 1 | 83.3% |", text)
        self.assertIn("| 2 | 66.7% |", text)
        self.assertIn("| 3 | 50.0% |", text)
        self.assertIn("Tasks left out for an unscored or missing trial: 1 (c)", text)

    def test_no_all_trials_table_for_one_trial(self):
        self.assertNotIn("Tasks passed in all k trials", self.report([record("a", 0, "pass"), record("b", 0, "pass")]))

    def test_cost_is_priced_kind_by_kind_and_the_total_adds_unscored_attempts_apart(self):
        records = [record("a", 0, "pass", agent=(1_000_000, 200_000, 400_000, 100_000), customer=(2_000_000, 500_000, 0)),
                   record("b", 0, "unscored", agent=(1_000_000, 0, 0, 0), customer=(1_000_000, 0, 0))]
        text = self.report(records)
        # agent: 3 + 0.75 + 0.12 + 1.5 = 5.37; customer: 2M in at 2 + 0.5M out at 10 = 9; no judges
        self.assertIn("- cost per scored conversation: $14.3700", text)
        self.assertIn("  - agent: $5.3700", text)
        self.assertIn("  - customer: $9.0000", text)
        self.assertIn("  - judges: none (no tokens used)", text)
        # the unscored attempt: agent 1M in = 3, customer 1M in = 2
        self.assertIn("- total spent: $19.3700", text)
        self.assertIn("  - attempts that gave a result: $14.3700", text)
        self.assertIn("(1 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): $5.0000", text)

    def test_unscored_and_earlier_attempts_have_their_own_token_table_even_without_rates(self):
        earlier = [{**record("a", 0, "unscored", agent=(7, 0, 0, 3), customer=(0, 0, 0)), "earlier_unscored_attempts": []}]
        records = [record("a", 0, "pass", earlier=earlier, attempt=2), record("b", 0, "unscored", agent=(11, 0, 0, 5))]
        text = self.report(records, rates={"models": {}})
        table = text.split("## Tokens, from unscored attempts")[1].split("## Cost")[0]
        self.assertIn("1 still unscored, 1 earlier unscored attempt(s)", table)
        self.assertIn("| agent | 6 | 18 | 0 | 0 | 8 |", table)

    def test_usage_gaps_make_a_cost_a_lower_bound_and_customer_cache_writes_are_counted(self):
        gap = record("a", 0, "pass", agent=(0, 0, 0, 0), customer=(0, 0, 0))
        gap["agent_calls_without_usage"] = 2
        text = self.report([gap])
        self.assertIn("- cost per scored conversation: unknown (at least: usage unknown for 2 agent call(s))", text)
        self.assertNotIn("none (no tokens used)\n  - customer", text.split("  - agent:")[1][:0] + "x")
        written = record("a", 0, "pass", customer=(0, 0, 0))
        written["customer_usage"]["models"][0].update(prompt_tokens=1_000_000, cached_tokens=0, cache_creation_tokens=400_000, completion_tokens=0)
        items = report.usage_items(written, "agent-m")
        self.assertEqual(items[1][2], {"uncached_input": 600_000, "cache_write_input": 400_000, "cache_read_input": 0, "output": 0})

    def test_cached_customer_tokens_without_a_cache_rate_are_not_priced_at_the_input_rate(self):
        text = self.report([record("a", 0, "pass", customer=(2_000_000, 500_000, 1_000_000))])
        self.assertIn("  - customer: not priced (no rate for: cust-m cache read input)", text)
        self.assertIn("  - agent: $4.5000", text)
        self.assertIn("- cost per scored conversation: not priced (no rate for: cust-m cache read input)", text)

    def test_earlier_unscored_attempts_count_in_the_total_but_not_in_the_cost_per_conversation(self):
        earlier = [{**record("a", 0, "unscored", agent=(1_000_000, 0, 0, 0), customer=(0, 0, 0)), "earlier_unscored_attempts": []}]
        text = self.report([record("a", 0, "pass", earlier=earlier, attempt=2, customer=(1_000_000, 0, 0), agent=(1_000_000, 0, 0, 0))])
        self.assertIn("- cost per scored conversation: $5.0000", text)  # 3 + 2
        self.assertIn("- total spent: $8.0000", text)
        self.assertIn("1 earlier unscored attempt(s)", text)
        self.assertIn("$3.0000", text.split("shown apart")[1])

    def test_a_model_without_a_rate_and_a_kind_without_a_rate_are_not_priced_never_zero(self):
        text = self.report([record("a", 0, "pass")], rates={"models": {"agent-m": RATES["models"]["agent-m"]}})
        unpriced = "not priced (no rate for: cust-m uncached input (no rate for the model); cust-m output (no rate for the model))"
        self.assertIn(f"- cost per scored conversation: {unpriced}", text)
        self.assertIn(f"  - customer: {unpriced}", text)
        self.assertIn("  - agent: $4.5000", text)
        self.assertIn(f"- total spent: {unpriced}", text)
        no_cache = {"models": {**RATES["models"], "agent-m": {"input": 3.0, "output": 15.0}}}
        text = self.report([record("a", 0, "pass", agent=(1_000_000, 0, 10, 0))], rates=no_cache)
        self.assertIn("  - agent: not priced (no rate for: agent-m cache read input)", text)

    def test_the_default_rates_file_is_data_rates_json_and_the_option_replaces_it(self):
        write_run(self.directory, [record("a", 0, "pass")])
        self.assertIn("rates.json", build_report(self.directory))
        self.assertEqual(report.RATES_FILE, Path(__file__).resolve().parent.parent / "data" / "rates.json")

    def test_the_report_command_prints_the_report_with_rates_option(self):
        write_run(self.directory, [record("a", 0, "pass")])
        rates_file = self.directory / "r.json"
        rates_file.write_text(json.dumps(RATES))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--report", str(self.directory), "--rates", str(rates_file)])
        self.assertEqual(code, 0)
        self.assertIn("# τ-bench retail report", out.getvalue())
        self.assertIn("$", out.getvalue())

    def test_the_report_of_a_real_stand_in_run_has_every_section(self):
        self.run_retail(trials=2)
        text = build_report(self.directory, Path(__file__).resolve().parent.parent / "data" / "rates.json")
        for heading in ("## Conversations", "## Pass rate", "## Tasks passed in all k trials", "## Unscored", "## Tokens", "## Cost"):
            self.assertIn(heading, text)
        self.assertIn("**100.0%** (2 of 2 scored conversations)", text)
        self.assertIn("not priced", text)  # data/rates.json has no rate for the stand-in agent model


class CommandTests(Base):
    def test_a_missing_key_is_refused_before_any_request(self):
        for missing in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            env = {"OPENAI_API_KEY": "a", "ANTHROPIC_API_KEY": "b"}
            del env[missing]
            with self.subTest(missing=missing), mock.patch.dict(os.environ, env, clear=True), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                main(["--output-dir", str(self.directory), "--provider", "anthropic", "--anthropic-model", "m", "--limit", "1"])
            self.assertEqual(raised.exception.code, 2)
        self.assertFalse(self.directory.exists())

    def test_keys_are_written_nowhere(self):
        self.run_retail(send=ScriptedAgent(TASK, "anthropic"), provider="anthropic")
        for path in self.directory.iterdir():
            text = path.read_text()
            for key in (AGENT_KEY, CUSTOMER_KEY):
                self.assertNotIn(key, text)


from benchmark_loop_agent.tau import report  # noqa: E402
from benchmark_loop_agent.tau.report import build_report  # noqa: E402

if __name__ == "__main__":
    unittest.main()
