from __future__ import annotations

import re
import webbrowser
from collections.abc import Callable, Mapping

from jarvis.skills.base import normalize

DEFAULT_SITES: dict[str, tuple[str, str]] = {
    # spoken name -> (display name, URL)
    "youtube": ("YouTube", "https://www.youtube.com"),
    "google": ("Google", "https://www.google.com"),
    "gmail": ("Gmail", "https://mail.google.com"),
    "github": ("GitHub", "https://github.com"),
    "wikipedia": ("Wikipedia", "https://www.wikipedia.org"),
    "stack overflow": ("Stack Overflow", "https://stackoverflow.com"),
    "reddit": ("Reddit", "https://www.reddit.com"),
    "netflix": ("Netflix", "https://www.netflix.com"),
    "spotify": ("Spotify", "https://open.spotify.com"),
    "amazon": ("Amazon", "https://www.amazon.com"),
    "maps": ("Google Maps", "https://maps.google.com"),
    "google maps": ("Google Maps", "https://maps.google.com"),
    "news": ("Google News", "https://news.google.com"),
    "claude": ("Claude", "https://claude.ai"),
}

_OPEN = re.compile(
    r"^(?:please |can you |could you )?(?:open|launch|go to|navigate to|take me to)\s+"
    r"(?:up\s+)?(?:the\s+)?(?P<target>.+?)(?:\s+(?:website|site|web site|page))?(?:\s+please)?$"
)
_DOMAIN = re.compile(r"^(?:https?://)?[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/\S*)?$")


def resolve_site(target: str, sites: Mapping[str, tuple[str, str]] = DEFAULT_SITES) -> tuple[str, str] | None:
    """Map a spoken target ("youtube", "example dot com") to (display name, URL)."""
    target = target.strip()
    if target in sites:
        return sites[target]
    domain = re.sub(r"\s+dot\s+", ".", target).replace(" ", "")
    if _DOMAIN.match(domain):
        url = domain if domain.startswith(("http://", "https://")) else f"https://{domain}"
        return domain.split("://")[-1], url
    return None


class WebsiteSkill:
    name = "websites"

    def __init__(
        self,
        sites: Mapping[str, tuple[str, str]] = DEFAULT_SITES,
        opener: Callable[[str], object] = webbrowser.open,
    ) -> None:
        self.sites = sites
        self.opener = opener

    def handle(self, text: str) -> str | None:
        match = _OPEN.match(normalize(text))
        if match is None:
            return None
        site = resolve_site(match["target"], self.sites)
        if site is None:
            # Not a site we know ("open the pod bay doors"): let Claude answer.
            return None
        name, url = site
        self.opener(url)
        return f"Opening {name}."
