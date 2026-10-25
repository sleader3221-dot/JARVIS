"""Turns a transcribed request into a reply: built-in commands, then skills, then Claude."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from jarvis.skills.base import SkillRouter, normalize

EXIT_PHRASES = {"goodbye", "good bye", "bye", "exit", "quit", "stop listening", "shut down", "go to sleep"}
FORGET_PHRASES = {"forget everything", "clear memory", "clear your memory", "reset", "new conversation"}


class BrainLike(Protocol):
    memory: object

    def ask(self, text: str) -> str: ...


@dataclass(frozen=True)
class Reply:
    text: str
    exit: bool = False


class Assistant:
    def __init__(self, brain: BrainLike, skills: SkillRouter) -> None:
        self.brain = brain
        self.skills = skills

    def respond(self, text: str | None) -> Reply | None:
        """Return the reply to a request, or None if there was nothing to answer."""
        if not text or not normalize(text):
            return None
        command = normalize(text)
        if command in EXIT_PHRASES:
            return Reply("Goodbye.", exit=True)
        if command in FORGET_PHRASES:
            self.brain.memory.clear()
            return Reply("Done. I've cleared our conversation.")
        skill_reply = self.skills.handle(text)
        if skill_reply is not None:
            return Reply(skill_reply)
        return Reply(self.brain.ask(text.strip()))
