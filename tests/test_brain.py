import unittest
from types import SimpleNamespace

import anthropic

from jarvis.brain import EMPTY_REPLY, FALLBACK_BETA, REFUSAL_REPLY, WEB_SEARCH_TOOL, Brain, extract_text
from jarvis.memory import ConversationMemory


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def response(*blocks, stop_reason="end_turn"):
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason, stop_details=None)


def fake_request():
    try:
        import httpx
    except ImportError:
        return None
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(cls, code):
    request = fake_request()
    if request is not None:
        import httpx

        resp = httpx.Response(code, request=request)
    else:
        resp = SimpleNamespace(status_code=code, request=None, headers={})
    return cls("boom", response=resp, body=None)


class FakeClient:
    """Records each messages.create call and replays queued responses (or raises queued errors)."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Snapshot the message list: the brain builds a new list per request.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def make_brain(*results, web_search=True, turns=10):
    client = FakeClient(*results)
    brain = Brain(client, ConversationMemory(turns), model="claude-opus-5-5", effort="low",
                  max_tokens=1024, web_search=web_search)
    return brain, client


class BrainTests(unittest.TestCase):
    def test_request_shape(self):
        brain, client = make_brain(response(text_block("Hello there.")))
        self.assertEqual(brain.ask("hi"), "Hello there.")
        call = client.calls[0]
        self.assertEqual(call["model"], "claude-opus-5-5")
        self.assertEqual(call["max_tokens"], 1024)
        self.assertEqual(call["output_config"], {"effort": "low"})
        self.assertEqual(call["betas"], [FALLBACK_BETA])
        self.assertEqual(call["extra_body"], {"fallbacks": "default"})
        self.assertEqual(call["tools"], [WEB_SEARCH_TOOL])
        self.assertEqual(call["messages"], [{"role": "user", "content": "hi"}])
        self.assertIn("JARVIS", call["system"])
        self.assertNotIn("temperature", call)
        self.assertNotIn("thinking", call)

    def test_no_tools_when_web_search_disabled(self):
        brain, client = make_brain(response(text_block("ok")), web_search=False)
        brain.ask("hi")
        self.assertNotIn("tools", client.calls[0])

    def test_history_is_sent_and_trimmed(self):
        brain, client = make_brain(*(response(text_block(f"a{i}")) for i in range(3)), turns=2)
        for i in range(3):
            brain.ask(f"q{i}")
        self.assertEqual(
            client.calls[2]["messages"],
            [
                {"role": "user", "content": "q0"},
                {"role": "assistant", "content": "a0"},
                {"role": "user", "content": "q1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "q2"},
            ],
        )
        self.assertEqual(len(brain.memory), 2)

    def test_joins_cited_text_blocks_and_skips_tool_blocks(self):
        blocks = [
            SimpleNamespace(type="server_tool_use", name="web_search"),
            SimpleNamespace(type="web_search_tool_result", content=[]),
            text_block("The answer is "),
            text_block("forty two"),
            text_block(" according to the guide."),
        ]
        brain, _ = make_brain(response(*blocks))
        self.assertEqual(brain.ask("q"), "The answer is forty two according to the guide.")

    def test_pause_turn_is_resumed(self):
        paused = response(text_block("Let me check."), stop_reason="pause_turn")
        brain, client = make_brain(paused, response(text_block("It is sunny.")))
        self.assertEqual(brain.ask("weather?"), "Let me check. It is sunny.")
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(client.calls[1]["messages"][-1], {"role": "assistant", "content": paused.content})
        # Memory stores only the final text, never the raw content blocks.
        self.assertEqual(brain.memory.messages()[-1], {"role": "assistant", "content": "Let me check. It is sunny."})

    def test_refusal_not_remembered(self):
        brain, _ = make_brain(response(stop_reason="refusal"))
        self.assertEqual(brain.ask("something bad"), REFUSAL_REPLY)
        self.assertEqual(len(brain.memory), 0)

    def test_empty_reply(self):
        brain, _ = make_brain(response())
        self.assertEqual(brain.ask("q"), EMPTY_REPLY)
        self.assertEqual(len(brain.memory), 0)

    def test_api_errors_become_spoken_messages(self):
        cases = [
            (status_error(anthropic.AuthenticationError, 401), "ANTHROPIC_API_KEY"),
            (status_error(anthropic.RateLimitError, 429), "rate limited"),
            (status_error(anthropic.InternalServerError, 500), "status 500"),
            (anthropic.APIConnectionError(request=fake_request()), "internet connection"),
        ]
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                brain, _ = make_brain(error)
                self.assertIn(expected, brain.ask("hi"))
                self.assertEqual(len(brain.memory), 0)

    def test_extract_text_normalizes_whitespace(self):
        self.assertEqual(extract_text([text_block(" a \n b "), SimpleNamespace(type="thinking")]), "a b")


if __name__ == "__main__":
    unittest.main()
