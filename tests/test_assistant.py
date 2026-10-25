import unittest

from jarvis.assistant import Assistant
from jarvis.audio.tts import clean_for_speech
from jarvis.memory import ConversationMemory
from jarvis.skills import SkillRouter


class FakeBrain:
    def __init__(self):
        self.memory = ConversationMemory()
        self.asked = []

    def ask(self, text):
        self.asked.append(text)
        return f"Claude says: {text}"


class EchoSkill:
    name = "echo"

    def handle(self, text):
        return "skill reply" if text.startswith("skill") else None


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.brain = FakeBrain()
        self.assistant = Assistant(self.brain, SkillRouter([EchoSkill()]))

    def test_empty_input(self):
        for text in (None, "", "   ", "?!"):
            with self.subTest(text=text):
                self.assertIsNone(self.assistant.respond(text))

    def test_exit(self):
        reply = self.assistant.respond("Goodbye!")
        self.assertTrue(reply.exit)

    def test_forget(self):
        self.brain.memory.add("q", "a")
        reply = self.assistant.respond("clear memory")
        self.assertFalse(reply.exit)
        self.assertEqual(len(self.brain.memory), 0)

    def test_skill_before_claude(self):
        self.assertEqual(self.assistant.respond("skill please").text, "skill reply")
        self.assertEqual(self.brain.asked, [])

    def test_falls_back_to_claude(self):
        self.assertEqual(self.assistant.respond("  tell me a joke ").text, "Claude says: tell me a joke")


class CleanForSpeechTests(unittest.TestCase):
    def test_strips_markdown(self):
        text = "**Sure!** Here's [the docs](https://example.com).\n- one\n- two\n```py\nprint(1)\n```"
        self.assertEqual(clean_for_speech(text), "Sure! Here's the docs. one two")

    def test_replaces_bare_urls(self):
        self.assertEqual(clean_for_speech("See https://example.com/x for more"), "See the link for more")


if __name__ == "__main__":
    unittest.main()
