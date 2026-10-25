"""Built-in skills that are handled locally, without calling Claude."""

from jarvis.skills.base import Skill, SkillRouter
from jarvis.skills.time_date import TimeDateSkill
from jarvis.skills.web_search import WebSearchSkill
from jarvis.skills.websites import WebsiteSkill

__all__ = ["Skill", "SkillRouter", "TimeDateSkill", "WebSearchSkill", "WebsiteSkill", "default_skills"]


def default_skills(search_url: str) -> SkillRouter:
    # Search runs before websites so "search for open source" isn't read as "open ...".
    return SkillRouter([TimeDateSkill(), WebSearchSkill(search_url), WebsiteSkill()])
