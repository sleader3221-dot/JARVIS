import unittest

from jarvis.memory import ConversationMemory


class ConversationMemoryTests(unittest.TestCase):
    def test_messages_alternate_roles(self):
        memory = ConversationMemory(5)
        memory.add("hi", "hello")
        memory.add("how are you", "great")
        self.assertEqual(
            memory.messages(),
            [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
                {"role": "user", "content": "how are you"},
                {"role": "assistant", "content": "great"},
            ],
        )

    def test_keeps_only_recent_turns(self):
        memory = ConversationMemory(2)
        for i in range(5):
            memory.add(f"q{i}", f"a{i}")
        self.assertEqual(len(memory), 2)
        self.assertEqual(memory.messages()[0], {"role": "user", "content": "q3"})

    def test_zero_turns_remembers_nothing(self):
        memory = ConversationMemory(0)
        memory.add("q", "a")
        self.assertEqual(memory.messages(), [])

    def test_clear(self):
        memory = ConversationMemory()
        memory.add("q", "a")
        memory.clear()
        self.assertEqual(len(memory), 0)


if __name__ == "__main__":
    unittest.main()
