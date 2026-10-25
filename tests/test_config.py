import unittest

from jarvis.config import DEFAULT_MODEL, Config, ConfigError


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        config = Config.from_env({"ANTHROPIC_API_KEY": "sk-test"})
        self.assertEqual(config.api_key, "sk-test")
        self.assertEqual(config.model, DEFAULT_MODEL)
        self.assertEqual(config.mode, "wake")
        self.assertEqual(config.memory_turns, 10)
        self.assertTrue(config.web_search)
        self.assertEqual(config.wake_words, ("jarvis", "jervis"))

    def test_missing_key_is_none(self):
        self.assertIsNone(Config.from_env({}).api_key)
        self.assertIsNone(Config.from_env({"ANTHROPIC_API_KEY": ""}).api_key)

    def test_overrides(self):
        config = Config.from_env(
            {
                "JARVIS_MODEL": "claude-sonnet-5-5",
                "JARVIS_EFFORT": "Medium",
                "JARVIS_MEMORY_TURNS": "3",
                "JARVIS_WEB_SEARCH": "off",
                "JARVIS_MODE": "ptt",
                "JARVIS_WAKE_WORDS": "Friday, computer ,",
                "JARVIS_SEARCH_URL": "https://duckduckgo.com/?q={query}",
            }
        )
        self.assertEqual(config.model, "claude-sonnet-5-5")
        self.assertEqual(config.effort, "medium")
        self.assertEqual(config.memory_turns, 3)
        self.assertFalse(config.web_search)
        self.assertEqual(config.mode, "ptt")
        self.assertEqual(config.wake_words, ("friday", "computer"))
        self.assertEqual(config.search_url, "https://duckduckgo.com/?q={query}")

    def test_invalid_values(self):
        for env in (
            {"JARVIS_MODE": "telepathy"},
            {"JARVIS_EFFORT": "extreme"},
            {"JARVIS_MEMORY_TURNS": "lots"},
            {"JARVIS_MEMORY_TURNS": "-1"},
            {"JARVIS_WEB_SEARCH": "maybe"},
            {"JARVIS_SEARCH_URL": "https://example.com/search"},
        ):
            with self.subTest(env=env), self.assertRaises(ConfigError):
                Config.from_env(env)


if __name__ == "__main__":
    unittest.main()
