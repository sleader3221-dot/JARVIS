from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol


class Skill(Protocol):
    name: str

    def handle(self, text: str) -> str | None:
        """Return a spoken reply if this skill handles `text`, otherwise None."""


def normalize(text: str) -> str:
    """Lowercase, collapse whitespace and drop surrounding punctuation."""
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text.strip(" .,!?;:")


class SkillRouter:
    def __init__(self, skills: Iterable[Skill]) -> None:
        self.skills = list(skills)

    def handle(self, text: str) -> str | None:
        for skill in self.skills:
            reply = skill.handle(text)
            if reply is not None:
                return reply
        return None
