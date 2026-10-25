"""Short-term conversation memory."""

from __future__ import annotations

from collections import deque


class ConversationMemory:
    """Rolling window of the most recent user/assistant exchanges.

    Exchanges are stored as plain text only (no thinking or tool-use blocks), so
    dropping the oldest exchange never leaves an orphaned tool call or a thinking
    block whose conversation prefix has changed.
    """

    def __init__(self, max_turns: int = 10) -> None:
        self._turns: deque[tuple[str, str]] = deque(maxlen=max_turns)

    def add(self, user_text: str, assistant_text: str) -> None:
        self._turns.append((user_text, assistant_text))

    def messages(self) -> list[dict[str, str]]:
        """The remembered exchanges in Messages API format, oldest first."""
        out: list[dict[str, str]] = []
        for user_text, assistant_text in self._turns:
            out.append({"role": "user", "content": user_text})
            out.append({"role": "assistant", "content": assistant_text})
        return out

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
