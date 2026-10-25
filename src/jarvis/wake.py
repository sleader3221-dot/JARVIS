"""Wake-word detection on transcribed speech."""

from __future__ import annotations

import re
from collections.abc import Iterable


class WakeWordDetector:
    """Spots a wake word (optionally preceded by "hey"/"ok") in a transcript.

    Detection runs on the speech-to-text output, so no extra wake-word engine or
    API key is needed. Add common misrecognitions as extra wake words.
    """

    def __init__(self, wake_words: Iterable[str]) -> None:
        words = [w.strip() for w in wake_words if w.strip()]
        if not words:
            raise ValueError("at least one wake word is required")
        alternatives = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
        self._pattern = re.compile(
            rf"\b(?:(?:hey|hi|ok|okay)[\s,]+)?(?:{alternatives})(?:'s)?\b[\s,.!?:;-]*",
            re.IGNORECASE,
        )

    def extract(self, transcript: str | None) -> str | None:
        """Return the command spoken after the wake word ("" if none), or None if absent."""
        if not transcript:
            return None
        match = self._pattern.search(transcript)
        if match is None:
            return None
        return transcript[match.end():].strip()
