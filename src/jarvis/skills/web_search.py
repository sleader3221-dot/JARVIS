from __future__ import annotations

import re
import webbrowser
from collections.abc import Callable
from urllib.parse import quote_plus

from jarvis.skills.base import normalize

DEFAULT_SEARCH_URL = "https://www.google.com/search?q={query}"

_SEARCH = re.compile(
    r"^(?:please |can you |could you )?"
    r"(?:search (?:the web |online |google |the internet )?for|search|google|look up)\s+(?P<query>.+)$"
)


class WebSearchSkill:
    """Opens a web search in the browser ("search for ...", "google ...", "look up ...").

    Questions that merely need fresh information ("who won the match last night?")
    go to Claude instead, which can use its own web search tool to answer aloud.
    """

    name = "web_search"

    def __init__(
        self,
        url_template: str = DEFAULT_SEARCH_URL,
        opener: Callable[[str], object] = webbrowser.open,
    ) -> None:
        self.url_template = url_template
        self.opener = opener

    def handle(self, text: str) -> str | None:
        match = _SEARCH.match(normalize(text))
        if match is None:
            return None
        query = match["query"].strip()
        self.opener(self.url_template.format(query=quote_plus(query)))
        return f"Here are the search results for {query}."
