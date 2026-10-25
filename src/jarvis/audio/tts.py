"""Text-to-speech using pyttsx3 (SAPI5 voices on Windows, works offline)."""

from __future__ import annotations

import re

_MARKDOWN = [
    (re.compile(r"```.*?```", re.DOTALL), " "),  # code blocks
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), r"\1"),  # [text](url) -> text
    (re.compile(r"https?://\S+"), "the link"),
    (re.compile(r"[*_`#>]+"), ""),  # emphasis, headings, quotes
    (re.compile(r"^\s*[-•]\s+", re.MULTILINE), ""),  # bullets
]


def clean_for_speech(text: str) -> str:
    """Remove markdown and URLs that sound bad when read aloud."""
    for pattern, replacement in _MARKDOWN:
        text = pattern.sub(replacement, text)
    return re.sub(r"\s+", " ", text).strip()


class TextToSpeech:
    def __init__(self, rate: int = 185, voice: str | None = None) -> None:
        import pyttsx3

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        if voice:
            for v in self.engine.getProperty("voices"):
                if voice.lower() in (v.name or "").lower():
                    self.engine.setProperty("voice", v.id)
                    break

    def say(self, text: str) -> None:
        self.engine.say(clean_for_speech(text))
        self.engine.runAndWait()
