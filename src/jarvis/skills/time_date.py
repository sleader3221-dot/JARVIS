from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime

from jarvis.skills.base import normalize

_TIME = re.compile(
    r"\bwhat(?:'s| is)? (?:the )?(?:current )?time\b|\btime is it\b|\btell me the time\b|\bcurrent time\b"
)
_DATE = re.compile(
    r"\bwhat(?:'s| is)? (?:the |today's )?(?:current )?date\b|\bwhat day is (?:it|today)\b"
    r"|\btoday's date\b|\bwhat's today\b|\btell me the date\b|\bthe date today\b"
)


def format_time(now: datetime) -> str:
    hour = now.hour % 12 or 12
    return f"It's {hour}:{now.minute:02d} {'AM' if now.hour < 12 else 'PM'}."


def format_date(now: datetime) -> str:
    return f"Today is {now:%A}, {now:%B} {now.day}, {now.year}."


class TimeDateSkill:
    name = "time_date"

    def __init__(self, clock: Callable[[], datetime] = datetime.now) -> None:
        self.clock = clock

    def handle(self, text: str) -> str | None:
        text = normalize(text)
        wants_time = bool(_TIME.search(text))
        wants_date = bool(_DATE.search(text))
        if not (wants_time or wants_date):
            return None
        now = self.clock()
        parts = []
        if wants_time:
            parts.append(format_time(now))
        if wants_date:
            parts.append(format_date(now))
        return " ".join(parts)
