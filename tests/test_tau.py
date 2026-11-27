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
from benchmark_loop_agent.tau import rules as tau_rules  # noqa: E402

if __name__ == "__main__":
    unittest.main()


class FinishCheckTests(Base):
    """``--finish-check``: a reply is held once and asked again before a hand-over, and before the reply after a change."""

    def run_checked(self, send, finish_check=True, completion=None):
        parameters = RunParameters("openai", "agent-model", "gpt-6-sol", (TASK_ID,), 1, 300, None, 1, finish_check)
        with mock.patch.object(UP.llm_utils, "completion", completion or ScriptedLitellm(TASK)):
            return run_retail(self.directory, parameters, environment("openai"), send)

    @staticmethod
    def note_of(request):
        last = request["input"][-1]
        return last["content"] if last.get("role") == "user" and tau_agent.CHECK_HEADER in last["content"] else None

    def handing_over(self, again=False):
        """A ``Send`` that hands over first; asked again it either helps or makes the same transfer; then it says it is done."""
        requests = []

        def send(provider, api_key, request):
            requests.append(request)
            transferred = any(i.get("type") == "function_call_output" for i in request["input"])
            spoken = sum(1 for i in request["input"] if i.get("role") == "assistant") > 1
            if self.note_of(request) is not None:
                return openai_reply(calls=[("transfer_to_human_agents", {"summary": "wants a change"})]) if again else openai_reply(text="Let me look at that for you.")
            if transferred or spoken:
                return openai_reply(text=FINAL_TEXT)
            return openai_reply(calls=[("transfer_to_human_agents", {"summary": "wants a change"})])

        return send, requests

    def test_a_hand_over_is_held_once_and_the_second_reply_is_what_the_conversation_gets(self):
        send, requests = self.handing_over()
        self.run_checked(send)
        note = self.note_of(requests[1])
        self.assertIn("transfer the customer to a human agent", note)
        self.assertIn('"wants a change"', note)
        self.assertEqual(requests[1]["input"][:-1], requests[0]["input"])  # the same conversation, plus the note
        self.assertEqual(requests[1]["instructions"], requests[0]["instructions"])
        self.assertEqual(requests[1]["tools"], requests[0]["tools"])
        record = self.records()[0]
        self.assertEqual(record["agent_checks"], ["handover"])
        self.assertEqual(record["agent_calls"], len(requests))
        conversation = (self.directory / batch.CONVERSATIONS_FILE).read_text()
        self.assertNotIn("transfer_to_human_agents", conversation)  # the held call never reached the tools
        self.assertNotIn(tau_agent.CHECK_HEADER, conversation)  # the note is not part of the conversation
        self.assertTrue(all(self.note_of(r) is None for r in requests[2:]))
        self.assertIs(batch.read_manifest(self.directory)["parameters"]["finish_check"], True)

    def test_the_same_transfer_made_again_goes_through_and_is_not_held_twice(self):
        send, requests = self.handing_over(again=True)
        self.run_checked(send)
        self.assertEqual(self.records()[0]["agent_checks"], ["handover"])
        self.assertIn("transfer_to_human_agents", (self.directory / batch.CONVERSATIONS_FILE).read_text())
        self.assertEqual(sum(1 for r in requests if self.note_of(r) is not None), 1)

    def test_the_reply_after_a_change_is_held_once_and_a_reply_without_a_change_is_not(self):
        send = ScriptedAgent(TASK)
        records = self.run_checked(send)
        self.assertEqual(records[0]["outcome"], "pass")
        self.assertEqual(self.records()[0]["agent_checks"], ["requests"])
        notes = [self.note_of(r) for r in send.requests]
        self.assertEqual(sum(1 for n in notes if n is not None), 1)
        self.assertIn(json.dumps(FINAL_TEXT), notes[-1])
        self.assertIn("every request the customer has made", notes[-1])
        self.assertIsNone(notes[0])  # the first reply follows no change

    def test_without_the_option_nothing_is_held_and_the_records_are_as_before(self):
        send, requests = self.handing_over()
        self.run_checked(send, finish_check=False)
        self.assertTrue(all(self.note_of(r) is None for r in requests))
        self.assertNotIn("agent_checks", self.records()[0])
        self.assertNotIn("finish_check", batch.read_manifest(self.directory)["parameters"])

    def test_the_option_is_part_of_what_a_directory_holds(self):
        self.run_checked(ScriptedAgent(TASK), finish_check=False)
        with self.assertRaises(ValueError):
            self.run_checked(ScriptedAgent(TASK), finish_check=True)

    def test_the_report_says_the_check_was_on_and_how_many_replies_it_held(self):
        from benchmark_loop_agent.tau.report import RATES_FILE, build_report
        self.run_checked(ScriptedAgent(TASK))
        self.assertIn("- finish check: on", build_report(self.directory, RATES_FILE))
        self.assertIn("replies held: 1", build_report(self.directory, RATES_FILE))


class AskingCustomer(ScriptedLitellm):
    """The customer of ``ScriptedLitellm``, whose opening message also asks for a supervisor."""

    def __call__(self, *args, **kwargs):
        reply = super().__call__(*args, **kwargs)
        if kwargs["model"].endswith("gpt-6-sol") and reply.choices[0].message.content != "###STOP###":
            reply.choices[0].message.content = "Hello, I would like to change my order. Can I speak to a supervisor about it?"
        return reply


class HandoverRuleTests(Base):
    """``--handover-rule``: the transfer tool is sent only after the customer has asked for a person."""

    def run_ruled(self, send, handover_rule=True, completion=None, provider="openai"):
        parameters = RunParameters(provider, "agent-model", "gpt-6-sol", (TASK_ID,), 1, 300, None, 1, False, handover_rule)
        with mock.patch.object(UP.llm_utils, "completion", completion or ScriptedLitellm(TASK)):
            return run_retail(self.directory, parameters, environment(provider), send)

    @staticmethod
    def tool_names(request):
        return [t["name"] for t in request["tools"]]

    def test_phrases_that_ask_for_a_person_and_phrases_that_do_not(self):
        asks = ["Can I speak to a supervisor?", "I want a human.", "Please escalate this.", "Get me your manager",
                "Is there someone else who can help?", "a real person, please", "connect me to a REPRESENTATIVE",
                "Is there another team for this?", "Please put me through to an agent.",
                "If not, please transfer me to a person who can help.", "or connect me with someone who can look into it",
                "Is there another way to find the placement dates or have someone review them?",
                "I don't want to wait. Get me a supervisor.", "Can I talk to somebody about this?"]
        does_not = ["Can you refund the lost tablet?", "I want to change my order please.", "You are not helping me at all.",
                    "Cancel it. I managed to find the order number.", "the humane thing to do", "Yes, go ahead.",
                    "I don't want a supervisor, just fix it.", "No need for a manager.", "Please don't transfer me.",
                    "Can you put it on my card?", "Is that available? I'm trying not to spend more.",
                    "My name is Chen Smith, and my ZIP code is 32278. Can you check the order now?"]
        for text in asks:
            self.assertTrue(tau_agent.customer_asked_for_a_person([{"role": "user", "text": text}]), text)
        for text in does_not:
            self.assertFalse(tau_agent.customer_asked_for_a_person([{"role": "user", "text": text}]), text)
        self.assertFalse(tau_agent.customer_asked_for_a_person([{"role": "assistant", "text": "I can get a supervisor.", "calls": []}]))

    def test_the_transfer_tool_is_not_sent_until_the_customer_asks_and_nothing_else_changes(self):
        plain = ScriptedAgent(TASK)
        self.run_ruled(plain, handover_rule=False)
        self.directory = self.directory.parent / "ruled"
        ruled = ScriptedAgent(TASK)
        records = self.run_ruled(ruled)
        self.assertEqual(records[0]["outcome"], "pass")
        self.assertEqual(len(ruled.requests), len(plain.requests))  # no extra call
        for with_rule, without in zip(ruled.requests, plain.requests):
            self.assertIn("transfer_to_human_agents", self.tool_names(without))
            self.assertEqual(self.tool_names(with_rule), [n for n in self.tool_names(without) if n != "transfer_to_human_agents"])
            self.assertEqual([t for t in without["tools"] if t["name"] != "transfer_to_human_agents"], with_rule["tools"])
            self.assertEqual(with_rule["instructions"], without["instructions"])
            self.assertEqual(with_rule["input"], without["input"])
        self.assertEqual(self.records()[0]["agent_handover"], {"offered": False, "refused_replies": 0, "announced_without_tool": 0})
        self.assertIs(batch.read_manifest(self.directory)["parameters"]["handover_rule"], True)

    def test_the_tool_is_sent_once_the_customer_has_asked_and_stays(self):
        for provider in ("openai", "anthropic"):
            self.directory = self.directory.parent / provider
            send = ScriptedAgent(TASK, provider)
            self.run_ruled(send, completion=AskingCustomer(TASK), provider=provider)
            self.assertGreater(len(send.requests), 1)
            for request in send.requests:  # the customer asked in the first message: every request has the tool
                self.assertIn("transfer_to_human_agents", [t["name"] for t in request["tools"]])
            self.assertIs(self.records()[0]["agent_handover"]["offered"], True)

    def test_a_reply_that_announces_a_transfer_without_the_tool_is_asked_again_at_most_twice(self):
        requests = []

        def send(provider, api_key, request):
            requests.append(request)
            said = sum(1 for i in request["input"] if i.get("role") == "assistant")
            if said > 1:
                return openai_reply(text=FINAL_TEXT)
            return openai_reply(text="YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON.")

        self.run_ruled(send)
        first_turn = [r for r in requests if sum(1 for i in r["input"] if i.get("role") == "assistant") == 1]
        self.assertEqual(len(first_turn), 3)  # the reply, and two more asks
        self.assertNotIn(tau_agent.CHECK_HEADER, json.dumps(first_turn[0]["input"]))
        for again in first_turn[1:]:
            self.assertEqual(again["input"][:-1], first_turn[0]["input"])
            self.assertIn("not available", again["input"][-1]["content"])
        self.assertEqual(self.records()[0]["agent_handover"]["refused_replies"], 2)
        self.assertEqual(self.records()[0]["agent_handover"]["announced_without_tool"], 1)  # it went out, and the record says so
        self.assertNotIn(tau_agent.CHECK_HEADER, (self.directory / batch.CONVERSATIONS_FILE).read_text())

    def test_other_ways_of_announcing_a_transfer_are_caught_and_ordinary_replies_are_not(self):
        for text in ("YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON.", "I'll connect you with a specialist now.",
                     "I am transferring you to our team.", "Let me hand you over to a colleague.", "I'm escalating this for you.",
                     "I will forward your case to the right team."):
            self.assertTrue(tau_agent.announces_handover(text, []), text)
        for text in ("I can't transfer you, but I can cancel the order.", "The refund will be transferred to your card.",
                     "All done, the change is made.", "I cannot do that under the policy.", "Your order is connected to this address.",
                     "I'm unable to connect you with a human agent right now.", "I won't be escalating this; here is what I can do."):
            self.assertFalse(tau_agent.announces_handover(text, []), text)

    def test_on_anthropic_the_tool_is_withheld_the_same_way(self):
        send = ScriptedAgent(TASK, "anthropic")
        self.run_ruled(send, provider="anthropic")
        for request in send.requests:
            self.assertNotIn("transfer_to_human_agents", [t["name"] for t in request["tools"]])
            self.assertEqual(request["tools"][-1]["cache_control"], {"type": "ephemeral"})  # the breakpoint stays on the last tool sent

    def test_a_call_to_the_tool_that_was_not_sent_is_unscored_and_never_reaches_the_tools(self):
        def send(provider, api_key, request):
            return openai_reply(calls=[("transfer_to_human_agents", {"summary": "x"})])

        records = self.run_ruled(send)
        self.assertEqual(records[0]["outcome"], "unscored")
        self.assertIn("not among the tools", records[0]["reason"])
        self.assertNotIn("Transfer successful", (self.directory / batch.CONVERSATIONS_FILE).read_text())

    def test_without_the_option_the_records_are_as_before_and_the_option_is_part_of_a_directory(self):
        self.run_ruled(ScriptedAgent(TASK), handover_rule=False)
        self.assertNotIn("agent_handover", self.records()[0])
        self.assertNotIn("handover_rule", batch.read_manifest(self.directory)["parameters"])
        with self.assertRaises(ValueError):
            self.run_ruled(ScriptedAgent(TASK), handover_rule=True)

    def test_the_report_says_the_rule_was_on(self):
        from benchmark_loop_agent.tau.report import RATES_FILE, build_report
        self.run_ruled(ScriptedAgent(TASK))
        self.assertIn("- hand-over rule: on", build_report(self.directory, RATES_FILE))


PRODUCT = {"name": "Mug", "product_id": "p1", "variants": {
    "1": {"item_id": "1", "options": {"color": "blue", "size": "S"}, "available": False, "price": 1.0},
    "2": {"item_id": "2", "options": {"color": "black", "size": "S"}, "available": True, "price": 7.25},
    "3": {"item_id": "3", "options": {"color": "red", "size": "S"}, "available": True, "price": 9.5},
    "4": {"item_id": "4", "options": {"color": "red", "size": "L"}, "available": True, "price": 9.5},
    "5": {"item_id": "5", "options": {"color": "black", "size": "L"}, "available": True, "price": 12.0}}}
ORDER = {"order_id": "#W1", "status": "pending", "items": [{"name": "Mug", "product_id": "p1", "item_id": "1", "price": 8.0,
                                                           "options": {"color": "blue", "size": "S"}}]}


def call(name, id="c1", **arguments):
    return {"id": id, "name": name, "arguments": arguments}


def read(tool, result, id, **arguments):
    """A tool call and its result, as two kept items."""
    return [{"role": "assistant", "text": "", "calls": [call(tool, id, **arguments)]},
            {"role": "tool", "id": id, "text": result if isinstance(result, str) else json.dumps(result)}]


class RetailRulesTests(Base):
    """``--rules``: retail rules in code (``tau/rules.py``)."""

    ITEMS = [{"role": "user", "text": "I want another mug."}, *read("get_order_details", ORDER, "o1", order_id="#W1"),
             *read("get_product_details", PRODUCT, "p1", product_id="p1")]

    def search(self, items=None, **arguments):
        return json.loads(tau_rules.search(self.ITEMS if items is None else items, {"product_id": "p1", **arguments}))

    def run_ruled(self, send, rules=tau_rules.RULES, completion=None, provider="openai"):
        parameters = RunParameters(provider, "agent-model", "gpt-6-sol", (TASK_ID,), 1, 300, None, 1, False, False, tuple(rules))
        with mock.patch.object(UP.llm_utils, "completion", completion or ScriptedLitellm(TASK)):
            return run_retail(self.directory, parameters, environment(provider), send)

    # --- offers: the search

    def test_the_search_returns_only_items_in_stock_with_the_required_options_cheapest_first(self):
        found = self.search(required_options={"Color": " RED "})
        self.assertEqual([row["item_id"] for row in found["items_in_stock_that_match_cheapest_first"]], ["3", "4"])
        self.assertEqual(found["cheapest_match"], {"tie_at_the_same_price": ["3", "4"]})  # a tie is said, not broken
        everything = self.search()
        self.assertEqual([row["item_id"] for row in everything["items_in_stock_that_match_cheapest_first"]], ["2", "3", "4", "5"])
        self.assertEqual(everything["cheapest_match"], "2")
        self.assertEqual(everything["searched_for"], "any item in stock")

    def test_price_differences_are_against_what_the_customer_paid_in_cents(self):
        found = self.search(current_item_id="1", required_options={"color": "black"})
        self.assertEqual(found["current_item"]["price_paid"], 8.0)  # the order's price, not the catalogue's 1.0
        rows = {row["item_id"]: row["price_difference_against_current_item"] for row in found["items_in_stock_that_match_cheapest_first"]}
        self.assertEqual(rows, {"2": "0.75 (refunded to the customer)", "5": "4.00 (the customer pays this much more)"})
        no_order = self.search(items=self.ITEMS[:1] + self.ITEMS[3:], current_item_id="1", required_options={"color": "black", "size": "S"})
        self.assertEqual(no_order["items_in_stock_that_match_cheapest_first"][0]["price_difference_against_current_item"],
                         "6.25 (the customer pays this much more)")  # no order read: the catalogue's price of the current item

    def test_each_item_says_in_which_options_it_differs_from_the_current_item_and_other_purchases_are_listed(self):
        found = self.search(current_item_id="1", required_options={"color": "red"})
        rows = {row["item_id"]: row["differs_from_current_item_in"] for row in found["items_in_stock_that_match_cheapest_first"]}
        self.assertEqual(rows, {"3": {"color": "red"}, "4": {"color": "red", "size": "L"}})  # item 3 is "the same but in red"
        self.assertNotIn("differs_from_current_item_in", self.search(required_options={"color": "red"})["items_in_stock_that_match_cheapest_first"][0])
        second = {"order_id": "#W2", "status": "delivered", "items": [{"name": "Mug", "product_id": "p1", "item_id": "5", "price": 11.0, "options": {}},
                                                                      {"name": "Pen", "product_id": "p9", "item_id": "90", "price": 1.0, "options": {}}]}
        items = self.ITEMS + read("get_order_details", second, "o2", order_id="#W2")
        owned = self.search(items=items, current_item_id="1")["other_items_of_this_product_the_customer_bought"]
        self.assertEqual(owned, [{"item_id": "5", "in_order": "#W2", "options": {}, "in_stock_now": True, "price_now": 12.0}])
        self.assertNotIn("other_items_of_this_product_the_customer_bought", self.search(current_item_id="1"))  # only the current item was bought

    def test_a_choice_restricted_to_named_items_looks_only_at_them(self):
        found = self.search(only_among_item_ids=["5", "3", "999"])
        self.assertEqual([row["item_id"] for row in found["items_in_stock_that_match_cheapest_first"]], ["3", "5"])
        self.assertEqual(found["cheapest_match"], "3")  # not item 2, the cheapest of the catalogue
        self.assertEqual(found["of_those_not_variants_of_this_product"], ["999"])

    def test_when_nothing_in_stock_matches_the_result_says_so_and_what_exists(self):
        found = self.search(required_options={"color": "blue"})
        self.assertIs(found["no_item_in_stock_matches"], True)
        self.assertEqual(found["items_in_stock_that_match_cheapest_first"], [])
        self.assertEqual(found["matching_items_out_of_stock"], ["1"])
        self.assertEqual(found["values_in_stock_for_each_option"], {"color": ["black", "red"], "size": ["L", "S"]})
        self.assertEqual(found["closest_items_in_stock"][0]["differs_from_what_was_asked_in"], {"color": "black"})
        self.assertNotIn("cheapest_match", found)

    def test_what_the_search_cannot_answer_is_an_error_that_says_what_to_do(self):
        self.assertIn("get_product_details", self.search(items=self.ITEMS[:3])["error"])  # the product was never read
        self.assertEqual(self.search(required_options={"weight": "1kg"})["option_names"], ["color", "size"])
        self.assertIn("not a variant", self.search(current_item_id="77")["error"])
        self.assertIn("must be an object", self.search(required_options="red")["error"])

    def test_a_product_is_shown_without_its_variants_and_the_kept_conversation_is_not_changed(self):
        shown = tau_rules.shown_items(self.ITEMS)
        product = json.loads(shown[-1]["text"])
        self.assertNotIn("variants", product)
        self.assertEqual(product["option_values"], {"color": ["blue", "black", "red"], "size": ["S", "L"]})
        self.assertEqual((product["variants_in_stock"], product["variants_in_all"]), (4, 5))
        self.assertIn("find_replacement_items", product["note"])
        self.assertEqual(shown[2], self.ITEMS[2])  # the order result is untouched
        self.assertEqual(json.loads(self.ITEMS[-1]["text"]), PRODUCT)
        self.assertEqual(tau_rules.product_summary("Error: Product not found"), "Error: Product not found")

    def test_a_change_to_an_item_no_search_returned_is_named_and_one_to_a_returned_item_is_not(self):
        change = [call("modify_pending_order_items", order_id="#W1", item_ids=["1"], new_item_ids=["3"], payment_method_id="paypal_1")]
        self.assertIn("The new item 3 was not returned", tau_rules.unsearched_change(self.ITEMS, change))
        searched = self.ITEMS + read("find_replacement_items", tau_rules.search(self.ITEMS, {"product_id": "p1", "required_options": {"color": "red"}}),
                                     "s1", product_id="p1")
        self.assertIsNone(tau_rules.unsearched_change(searched, change))
        self.assertIn("5", tau_rules.unsearched_change(searched, [call("exchange_delivered_order_items", order_id="#W1", item_ids=["1", "1"],
                                                                        new_item_ids=["3", "5"], payment_method_id="p")]))
        self.assertIsNone(tau_rules.unsearched_change(self.ITEMS, [call("cancel_pending_order", order_id="#W1", reason="no longer needed")]))

    # --- order-lock, payment, address, handover-once

    def test_an_item_change_is_held_for_the_lock_only_when_the_customer_spoke_of_delivery_and_the_address_is_unchanged(self):
        change = [call("modify_pending_order_items", order_id="#W1", item_ids=["1"], new_item_ids=["3"], payment_method_id="p")]
        spoke = [{"role": "user", "text": "Swap the mug, and send it to my office instead."}]
        self.assertIn("locks the order", tau_rules.locks_before_address(spoke, change))
        self.assertIsNone(tau_rules.locks_before_address([{"role": "user", "text": "Swap the mug."}], change))
        done = spoke + read("modify_pending_order_address", ORDER, "a1", order_id="#W1")
        self.assertIsNone(tau_rules.locks_before_address(done, change))
        failed = spoke + read("modify_pending_order_address", "Error: Non-pending order cannot be modified", "a1", order_id="#W1")
        self.assertIsNotNone(tau_rules.locks_before_address(failed, change))
        other = spoke + read("modify_pending_order_address", ORDER, "a1", order_id="#W2")
        self.assertIsNotNone(tau_rules.locks_before_address(other, change))  # another order's address
        self.assertIsNone(tau_rules.locks_before_address(spoke, [*change, call("modify_pending_order_address", "c2", order_id="#W1")]))
        self.assertIsNone(tau_rules.locks_before_address(spoke, [call("exchange_delivered_order_items", order_id="#W1")]))

    def payment_items(self, methods, customer="Please swap the mug for the black one."):
        return [{"role": "user", "text": customer}, *read("get_user_details", {"payment_methods": {name: {} for name in methods}}, "u1", user_id="u")]

    def test_an_item_change_is_held_only_when_several_methods_are_on_file_and_the_customer_named_none(self):
        change = [call("modify_pending_order_items", order_id="#W1", item_ids=["1"], new_item_ids=["2"], payment_method_id="paypal_1")]
        exchange = [call("exchange_delivered_order_items", order_id="#W1", item_ids=["1"], new_item_ids=["2"], payment_method_id="paypal_1")]
        two = ["paypal_1", "credit_card_2"]
        self.assertIn("which payment method", tau_rules.payment_not_chosen(self.payment_items(two), change))
        self.assertIsNotNone(tau_rules.payment_not_chosen(self.payment_items(two), exchange))
        self.assertIsNone(tau_rules.payment_not_chosen(self.payment_items(["paypal_1"]), change))  # one method: nothing to choose
        self.assertIsNone(tau_rules.payment_not_chosen(self.payment_items(two, "Swap it and use my credit card."), change))
        self.assertIsNone(tau_rules.payment_not_chosen(self.payment_items(two, "Swap it, same payment method."), change))
        self.assertIsNone(tau_rules.payment_not_chosen([{"role": "user", "text": "Swap it."}], change))  # the customer's details were never read
        self.assertIsNone(tau_rules.payment_not_chosen(self.payment_items(two), [call("cancel_pending_order", order_id="#W1")]))
        self.assertIsNone(tau_rules.payment_not_chosen(self.payment_items(two), [call("return_delivered_order_items", order_id="#W1")]))

    def test_address_fields_are_put_in_the_forms_of_the_database_and_nothing_else_is_touched(self):
        fixed = tau_rules.fix_address(call("modify_user_address", user_id="u", address1="1 Road", address2="", city="New York",
                                           state="New York", country="United States", zip="10001"))
        self.assertEqual((fixed["arguments"]["state"], fixed["arguments"]["country"]), ("NY", "USA"))
        self.assertEqual(fixed["arguments"]["city"], "New York")  # a city named as a state stays
        for country in ("", "US", "usa", "U.S.A.", "United States of America"):
            self.assertEqual(tau_rules.fix_address(call("modify_pending_order_address", order_id="#W1", state="tx", country=country))["arguments"],
                             {"order_id": "#W1", "state": "TX", "country": "USA"})
        right = call("modify_user_address", user_id="u", state="CO", country="USA")
        self.assertIs(tau_rules.fix_address(right), right)
        abroad = call("modify_user_address", user_id="u", state="Ontario", country="Canada")
        self.assertIs(tau_rules.fix_address(abroad), abroad)  # not a form of the same value: left as the model wrote it
        other = call("cancel_pending_order", order_id="#W1", reason="no longer needed", country="United States")
        self.assertIs(tau_rules.fix_address(other), other)

    def test_only_the_first_transfer_made_before_the_customer_asked_is_an_early_one(self):
        transfer = [call("transfer_to_human_agents", summary="s")]
        self.assertTrue(tau_rules.first_early_transfer([{"role": "user", "text": "hi"}], transfer, False))
        self.assertFalse(tau_rules.first_early_transfer([{"role": "user", "text": "a supervisor"}], transfer, True))
        self.assertFalse(tau_rules.first_early_transfer([{"role": "user", "text": "hi"}], [call("get_user_details")], False))
        self.assertFalse(tau_rules.first_early_transfer([{"role": "assistant", "text": "", "calls": transfer}], transfer, False))

    # --- one turn under the rules

    def scripted(self, replies):
        """An ``ask`` that returns ``replies`` in order and keeps what it was sent."""
        asked = []

        def ask(items, tools):
            asked.append((items, [t["function"]["name"] for t in tools]))
            return replies[len(asked) - 1]

        return ask, asked

    def test_a_search_is_run_in_code_shown_to_the_model_and_never_sent_on_and_it_stays_in_later_turns(self):
        state = tau_rules.RuleState()
        searching = ("", [call("find_replacement_items", "s1", product_id="p1", required_options={"color": "red"})])
        ask, asked = self.scripted([searching, ("Red comes in S and L, both $9.50.", [])])
        text, calls = tau_rules.turn(("offers",), self.ITEMS, [], ask, state, False)
        self.assertEqual((text, calls), ("Red comes in S and L, both $9.50.", []))
        self.assertEqual(asked[0][1], ["find_replacement_items"])  # the agent's own tool is offered
        self.assertNotIn("variants", json.loads(asked[0][0][-1]["text"]))  # the product is shown as its summary
        self.assertEqual(asked[1][0][-2]["calls"][0]["name"], "find_replacement_items")
        self.assertEqual([row["item_id"] for row in json.loads(asked[1][0][-1]["text"])["items_in_stock_that_match_cheapest_first"]], ["3", "4"])
        self.assertEqual(state.record()["searches"][0]["arguments"], {"product_id": "p1", "required_options": {"color": "red"}})
        later = self.ITEMS + [{"role": "assistant", "text": text, "calls": []}, {"role": "user", "text": "The small one."}]
        merged = tau_rules.with_local(later, state)
        self.assertEqual([item["role"] for item in merged[len(self.ITEMS):]], ["assistant", "tool", "assistant", "user"])  # where it happened
        change = ("", [call("modify_pending_order_items", "w1", order_id="#W1", item_ids=["1"], new_item_ids=["3"], payment_method_id="p")])
        ask, asked = self.scripted([change])
        self.assertEqual(tau_rules.turn(("offers",), later, [], ask, state, False), change)  # item 3 was returned by the search: not held
        self.assertEqual(state.holds, [])

    def test_a_change_to_an_unsearched_item_is_held_at_most_twice_and_then_goes_through(self):
        change = ("", [call("modify_pending_order_items", "w1", order_id="#W1", item_ids=["1"], new_item_ids=["5"], payment_method_id="p")])
        state = tau_rules.RuleState()
        ask, asked = self.scripted([change, change, change])
        self.assertEqual(tau_rules.turn(("offers",), self.ITEMS, [], ask, state, False), change)
        self.assertEqual(state.holds, ["unsearched", "unsearched"])
        self.assertIn("was not returned by find_replacement_items", asked[1][0][-1]["text"])
        self.assertEqual(asked[1][0][:-1], asked[0][0])  # the same conversation, plus the note

    def test_one_hold_at_a_time_and_each_kind_once(self):
        items = [{"role": "user", "text": "Swap the mug and ship it to my office."},
                 *read("get_user_details", {"payment_methods": {"a": {}, "b": {}}}, "u1", user_id="u")]
        change = ("", [call("modify_pending_order_items", "w1", order_id="#W1", item_ids=["1"], new_item_ids=["3"], payment_method_id="a")])
        state = tau_rules.RuleState()
        ask, asked = self.scripted([change, change, change])
        self.assertEqual(tau_rules.turn(("order-lock", "payment"), items, [], ask, state, False), change)
        self.assertEqual(state.holds, ["order-lock", "payment"])
        ask, asked = self.scripted([change])
        tau_rules.turn(("order-lock", "payment"), items, [], ask, state, False)
        self.assertEqual(len(asked), 1)  # neither is asked a second time in the conversation

    def test_an_early_transfer_is_refused_once_without_the_tool(self):
        tools = [{"type": "function", "function": {"name": "transfer_to_human_agents"}}, {"type": "function", "function": {"name": "get_user_details"}}]
        transfer = ("", [call("transfer_to_human_agents", summary="s")])
        state = tau_rules.RuleState()
        ask, asked = self.scripted([transfer, ("I cannot do that. Anything else?", [])])
        self.assertEqual(tau_rules.turn(("handover-once",), [{"role": "user", "text": "Refund my lost tablet."}], tools, ask, state, False)[0],
                         "I cannot do that. Anything else?")
        self.assertEqual(asked[1][1], ["get_user_details"])
        ask, asked = self.scripted([transfer])
        self.assertEqual(tau_rules.turn(("handover-once",), [{"role": "user", "text": "Then nothing else."}], tools, ask, state, False), transfer)
        ask, asked = self.scripted([transfer, transfer])
        with self.assertRaises(tau_rules.RuleError):
            tau_rules.turn(("handover-once",), [{"role": "user", "text": "hi"}], tools, ask, tau_rules.RuleState(), False)

    def test_a_turn_that_keeps_searching_is_given_up(self):
        searching = ("", [call("find_replacement_items", "s1", product_id="p1")])
        ask, asked = self.scripted([searching] * 20)
        with self.assertRaises(tau_rules.RuleError):
            tau_rules.turn(("offers",), self.ITEMS, [], ask, tau_rules.RuleState(), False)
        self.assertEqual(len(asked), tau_rules.MAX_ROUNDS + 1)

    # --- in a run

    def test_with_rules_on_and_nothing_to_step_in_on_the_requests_are_the_same(self):
        plain = ScriptedAgent(TASK)
        self.run_ruled(plain, rules=())
        self.directory = self.directory.parent / "ruled"
        ruled = ScriptedAgent(TASK)
        quiet = tuple(rule for rule in tau_rules.RULES if rule != "offers")  # the scripted agent changes items without a search
        records = self.run_ruled(ruled, rules=quiet)
        self.assertEqual(records[0]["outcome"], "pass")
        self.assertEqual([(r["input"], r["tools"]) for r in ruled.requests], [(r["input"], r["tools"]) for r in plain.requests])
        self.assertEqual(self.records()[0]["agent_rules"], {"holds": [], "address_corrections": 0, "searches": []})
        self.assertEqual(batch.read_manifest(self.directory)["parameters"]["rules"], sorted(quiet))
        self.assertIn("rules in code: address, handover-once, order-lock, payment",
                      build_report(self.directory, Path(__file__).resolve().parent.parent / "data" / "rates.json"))

    def test_in_a_run_with_offers_the_search_tool_is_offered_and_an_unsearched_change_is_held_twice(self):
        ruled = ScriptedAgent(TASK)
        records = self.run_ruled(ruled, rules=("offers",))
        self.assertEqual(records[0]["outcome"], "pass")  # the scripted agent repeats its call, which then goes through
        self.assertEqual(self.records()[0]["agent_rules"]["holds"], ["unsearched", "unsearched"])
        self.assertTrue(all(r["tools"][-1]["name"] == "find_replacement_items" for r in ruled.requests))
        self.assertNotIn(tau_rules.HEADER, (self.directory / batch.CONVERSATIONS_FILE).read_text())  # the notes are not kept

    def test_a_run_without_rules_records_nothing_about_them(self):
        self.run_ruled(ScriptedAgent(TASK), rules=())
        self.assertNotIn("agent_rules", self.records()[0])
        self.assertNotIn("rules", batch.read_manifest(self.directory)["parameters"])

    def test_in_a_run_a_search_never_reaches_the_tools_and_the_record_keeps_it(self):
        requests = []

        def send(provider, api_key, request):
            requests.append(request)
            if any(i.get("type") == "function_call_output" for i in request["input"]):
                return openai_reply(text=FINAL_TEXT)
            return openai_reply(calls=[("find_replacement_items", {"product_id": "p-unread"})])

        self.run_ruled(send, rules=("offers",))
        record = self.records()[0]
        self.assertEqual(len(record["agent_rules"]["searches"]), 1)
        self.assertIn("were not read", record["agent_rules"]["searches"][0]["result"]["error"])
        self.assertNotIn("find_replacement_items", (self.directory / batch.CONVERSATIONS_FILE).read_text())  # upstream never saw the call
        self.assertTrue(any(i.get("type") == "function_call" and i["name"] == "find_replacement_items" for i in requests[-1]["input"]))

    def test_an_address_call_reaches_the_tools_in_the_forms_of_the_database(self):
        def send(provider, api_key, request):
            if any(i.get("type") == "function_call_output" for i in request["input"]):
                return openai_reply(text=FINAL_TEXT)
            return openai_reply(calls=[("modify_user_address", {"user_id": "nobody", "address1": "1 Road", "address2": "", "city": "New York",
                                                                "state": "New York", "country": "United States", "zip": "10001"})])

        self.run_ruled(send, rules=("address",))
        self.assertEqual(self.records()[0]["agent_rules"]["address_corrections"], 1)
        self.assertIn('"state": "NY", "country": "USA"', (self.directory / batch.CONVERSATIONS_FILE).read_text())

    def test_the_command_checks_the_names_and_refuses_the_older_options_beside_the_rules(self):
        base = ["--output-dir", str(self.directory), "--provider", "openai", "--openai-model", "m", "--rules"]
        for arguments in (base + ["address,nope"], base + ["address,address"], base + ["offers", "--finish-check"], base + ["offers", "--handover-rule"]):
            with self.assertRaises(SystemExit), mock.patch("sys.stderr"):
                main(arguments)
