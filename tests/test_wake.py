import unittest

from jarvis.wake import WakeWordDetector


class WakeWordTests(unittest.TestCase):
    def setUp(self):
        self.detector = WakeWordDetector(["jarvis", "jervis"])

    def test_command_after_wake_word(self):
        cases = {
            "Jarvis what time is it": "what time is it",
            "hey Jarvis, open YouTube": "open YouTube",
            "okay jervis. tell me a joke": "tell me a joke",
            "um Jarvis search for pizza": "search for pizza",
        }
        for transcript, expected in cases.items():
            with self.subTest(transcript=transcript):
                self.assertEqual(self.detector.extract(transcript), expected)

    def test_wake_word_alone(self):
        self.assertEqual(self.detector.extract("Hey Jarvis!"), "")

    def test_no_wake_word(self):
        for transcript in ("what time is it", "jarvisville is a town", "", None):
            with self.subTest(transcript=transcript):
                self.assertIsNone(self.detector.extract(transcript))

    def test_requires_a_word(self):
        with self.assertRaises(ValueError):
            WakeWordDetector([" "])


if __name__ == "__main__":
    unittest.main()
