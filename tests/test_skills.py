import unittest
from datetime import datetime

from jarvis.skills import SkillRouter, TimeDateSkill, WebSearchSkill, WebsiteSkill, default_skills
from jarvis.skills.time_date import format_date, format_time
from jarvis.skills.websites import resolve_site


class TimeDateSkillTests(unittest.TestCase):
    def setUp(self):
        self.skill = TimeDateSkill(clock=lambda: datetime(2026, 10, 25, 15, 7))

    def test_time(self):
        for text in ("What time is it?", "what's the time", "tell me the time please"):
            with self.subTest(text=text):
                self.assertEqual(self.skill.handle(text), "It's 3:07 PM.")

    def test_date(self):
        for text in ("What's the date?", "what day is it today", "Today's date"):
            with self.subTest(text=text):
                self.assertEqual(self.skill.handle(text), "Today is Sunday, October 25, 2026.")

    def test_time_and_date(self):
        reply = self.skill.handle("what's the time and what's the date")
        self.assertEqual(reply, "It's 3:07 PM. Today is Sunday, October 25, 2026.")

    def test_unrelated(self):
        self.assertIsNone(self.skill.handle("how much time does it take to boil an egg"))

    def test_formatting_edges(self):
        self.assertEqual(format_time(datetime(2026, 1, 1, 0, 5)), "It's 12:05 AM.")
        self.assertEqual(format_time(datetime(2026, 1, 1, 12, 0)), "It's 12:00 PM.")
        self.assertEqual(format_date(datetime(2026, 1, 1)), "Today is Thursday, January 1, 2026.")


class WebsiteSkillTests(unittest.TestCase):
    def setUp(self):
        self.opened = []
        self.skill = WebsiteSkill(opener=self.opened.append)

    def test_known_site(self):
        self.assertEqual(self.skill.handle("Open YouTube."), "Opening YouTube.")
        self.assertEqual(self.opened, ["https://www.youtube.com"])

    def test_multi_word_site(self):
        self.assertEqual(self.skill.handle("please open stack overflow"), "Opening Stack Overflow.")

    def test_domain(self):
        self.assertEqual(self.skill.handle("go to example.com"), "Opening example.com.")
        self.assertEqual(self.skill.handle("open python dot org website"), "Opening python.org.")
        self.assertEqual(self.opened, ["https://example.com", "https://python.org"])

    def test_unknown_target_falls_through(self):
        self.assertIsNone(self.skill.handle("open the pod bay doors"))
        self.assertIsNone(self.skill.handle("what is an open source license"))
        self.assertEqual(self.opened, [])

    def test_resolve_site_keeps_scheme(self):
        self.assertEqual(resolve_site("http://localhost.dev"), ("localhost.dev", "http://localhost.dev"))


class WebSearchSkillTests(unittest.TestCase):
    def setUp(self):
        self.opened = []
        self.skill = WebSearchSkill("https://search.test/?q={query}", opener=self.opened.append)

    def test_search_phrases(self):
        for text in ("Search for best pizza near me", "search the web for best pizza near me",
                     "google best pizza near me", "look up best pizza near me"):
            with self.subTest(text=text):
                self.assertEqual(self.skill.handle(text), "Here are the search results for best pizza near me.")
        self.assertEqual(self.opened[-1], "https://search.test/?q=best+pizza+near+me")

    def test_query_is_url_encoded(self):
        self.skill.handle("search for C++ & rust?")
        self.assertEqual(self.opened, ["https://search.test/?q=c%2B%2B+%26+rust"])

    def test_unrelated(self):
        self.assertIsNone(self.skill.handle("who won the world cup"))


class RouterTests(unittest.TestCase):
    def test_first_match_wins(self):
        class Fixed:
            name = "fixed"

            def __init__(self, reply):
                self.reply = reply

            def handle(self, text):
                return self.reply

        self.assertEqual(SkillRouter([Fixed(None), Fixed("a"), Fixed("b")]).handle("x"), "a")
        self.assertIsNone(SkillRouter([Fixed(None)]).handle("x"))

    def test_search_takes_priority_over_open(self):
        router = default_skills("https://search.test/?q={query}")
        for skill in router.skills:
            skill.opener = lambda url: None
        self.assertEqual(router.handle("search for open source"), "Here are the search results for open source.")


if __name__ == "__main__":
    unittest.main()
