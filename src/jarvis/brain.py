"""The Claude-backed "brain": sends requests to the Claude API with short-term memory."""

from __future__ import annotations

import logging
import re
from typing import Any

import anthropic

from jarvis.config import Config
from jarvis.memory import ConversationMemory

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are JARVIS, a helpful, concise and slightly witty personal voice assistant.
Your replies are read aloud by a text-to-speech engine, so:
- Answer in one to three short sentences unless the user asks for more detail.
- Use plain spoken language: no markdown, lists, code blocks, URLs or emoji.
- Write numbers, units and symbols the way they should be spoken when that reads better.
When you use web search, give the answer directly and name a source only when it matters."""

WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}

# Server-side refusal fallback: if a safety classifier declines the request, the API
# re-runs it on Anthropic's recommended fallback model for that refusal category.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

# A server-tool turn (web search) can pause with stop_reason "pause_turn"; resume it
# at most this many times before giving up.
MAX_CONTINUATIONS = 3

REFUSAL_REPLY = "Sorry, I can't help with that one."
EMPTY_REPLY = "Sorry, I don't have an answer for that."


def extract_text(content: list[Any]) -> str:
    """Join the text blocks of a response (web-search citations split text into several blocks)."""
    text = "".join(block.text for block in content if getattr(block, "type", None) == "text")
    return re.sub(r"\s+", " ", text).strip()


class Brain:
    def __init__(
        self,
        client: Any,
        memory: ConversationMemory,
        *,
        model: str,
        effort: str = "low",
        max_tokens: int = 4096,
        web_search: bool = True,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self.client = client
        self.memory = memory
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.web_search = web_search
        self.system_prompt = system_prompt

    @classmethod
    def from_config(cls, config: Config) -> Brain:
        return cls(
            anthropic.Anthropic(api_key=config.api_key),
            ConversationMemory(config.memory_turns),
            model=config.model,
            effort=config.effort,
            max_tokens=config.max_tokens,
            web_search=config.web_search,
        )

    def ask(self, text: str) -> str:
        """Send `text` to Claude (with recent history) and return a speakable reply."""
        messages = self.memory.messages() + [{"role": "user", "content": text}]
        try:
            reply, remember = self._complete(messages)
        except anthropic.AuthenticationError:
            return "I couldn't sign in to the Claude API. Please check your ANTHROPIC_API_KEY."
        except anthropic.RateLimitError:
            return "I'm being rate limited right now. Please try again in a moment."
        except anthropic.APIStatusError as e:
            log.error("Claude API error %s: %s", e.status_code, e)
            return f"The Claude API returned an error, status {e.status_code}."
        except anthropic.APIConnectionError as e:
            log.error("Could not reach the Claude API: %s", e)
            return "I can't reach the Claude API. Please check your internet connection."
        if remember:
            self.memory.add(text, reply)
        return reply

    def _request(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
            # Thinking is adaptive by default; low effort keeps spoken replies snappy.
            "output_config": {"effort": self.effort},
            "betas": [FALLBACK_BETA],
            "extra_body": {"fallbacks": "default"},
        }
        if self.web_search:
            request["tools"] = [WEB_SEARCH_TOOL]
        return request

    def _complete(self, messages: list[dict[str, Any]]) -> tuple[str, bool]:
        """Return (reply, whether to store the exchange in memory)."""
        parts: list[str] = []
        for _ in range(MAX_CONTINUATIONS + 1):
            response = self.client.beta.messages.create(**self._request(messages))
            if response.stop_reason == "refusal":
                log.info("Request declined: %s", getattr(response, "stop_details", None))
                return REFUSAL_REPLY, False
            parts.append(extract_text(response.content))
            if response.stop_reason != "pause_turn":
                break
            messages = messages + [{"role": "assistant", "content": response.content}]
        reply = " ".join(p for p in parts if p)
        if not reply:
            return EMPTY_REPLY, False
        return reply, True
