"""Runtime configuration, read from environment variables (and an optional .env file)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_MODEL = "claude-opus-5-5"
MODES = ("wake", "ptt", "text")
EFFORTS = ("low", "medium", "high", "xhigh", "max")


class ConfigError(ValueError):
    """Raised when an environment variable has an invalid value."""


def _get_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ConfigError(f"{name} must be true or false, got {raw!r}")


def _get_int(env: Mapping[str, str], name: str, default: int, minimum: int = 0) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    return value


def _get_choice(env: Mapping[str, str], name: str, default: str, choices: tuple[str, ...]) -> str:
    value = (env.get(name) or default).strip().lower()
    if value not in choices:
        raise ConfigError(f"{name} must be one of {', '.join(choices)}, got {value!r}")
    return value


@dataclass(frozen=True)
class Config:
    api_key: str | None = None
    model: str = DEFAULT_MODEL
    effort: str = "low"
    max_tokens: int = 4096
    memory_turns: int = 10
    web_search: bool = True
    mode: str = "wake"
    wake_words: tuple[str, ...] = ("jarvis", "jervis")
    language: str = "en-US"
    tts_rate: int = 185
    tts_voice: str | None = None
    search_url: str = "https://www.google.com/search?q={query}"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Config:
        env = os.environ if env is None else env
        wake_words = tuple(
            w.strip().lower() for w in env.get("JARVIS_WAKE_WORDS", "").split(",") if w.strip()
        )
        search_url = env.get("JARVIS_SEARCH_URL") or cls.search_url
        if "{query}" not in search_url:
            raise ConfigError("JARVIS_SEARCH_URL must contain a {query} placeholder")
        return cls(
            api_key=env.get("ANTHROPIC_API_KEY") or None,
            model=env.get("JARVIS_MODEL") or DEFAULT_MODEL,
            effort=_get_choice(env, "JARVIS_EFFORT", cls.effort, EFFORTS),
            max_tokens=_get_int(env, "JARVIS_MAX_TOKENS", cls.max_tokens, minimum=1),
            memory_turns=_get_int(env, "JARVIS_MEMORY_TURNS", cls.memory_turns),
            web_search=_get_bool(env, "JARVIS_WEB_SEARCH", cls.web_search),
            mode=_get_choice(env, "JARVIS_MODE", cls.mode, MODES),
            wake_words=wake_words or cls.wake_words,
            language=env.get("JARVIS_LANGUAGE") or cls.language,
            tts_rate=_get_int(env, "JARVIS_TTS_RATE", cls.tts_rate, minimum=50),
            tts_voice=env.get("JARVIS_TTS_VOICE") or None,
            search_url=search_url,
        )
