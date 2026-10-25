"""Command-line entry point and the listen -> think -> speak loops."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable

from jarvis.assistant import Assistant
from jarvis.config import MODES, Config, ConfigError
from jarvis.wake import WakeWordDetector

log = logging.getLogger("jarvis")

GREETING = "JARVIS online. How can I help?"


def _speaker(enabled: bool, config: Config) -> Callable[[str], None]:
    tts = None
    if enabled:
        from jarvis.audio.tts import TextToSpeech

        tts = TextToSpeech(rate=config.tts_rate, voice=config.tts_voice)

    def speak(text: str) -> None:
        print(f"JARVIS: {text}", flush=True)
        if tts is not None:
            tts.say(text)

    return speak


def run_text(assistant: Assistant, speak: Callable[[str], None]) -> None:
    speak(GREETING)
    while True:
        try:
            text = input("You: ")
        except EOFError:
            return
        reply = assistant.respond(text)
        if reply is None:
            continue
        speak(reply.text)
        if reply.exit:
            return


def _listen(stt, speak: Callable[[str], None], **kwargs) -> str | None:
    from jarvis.audio.stt import SpeechServiceError

    try:
        return stt.listen(**kwargs)
    except SpeechServiceError as e:
        log.error("%s", e)
        speak("My speech recognition service is unavailable. Please check your internet connection.")
        return None


def run_push_to_talk(assistant: Assistant, speak: Callable[[str], None], config: Config) -> None:
    from jarvis.audio.stt import SpeechToText

    stt = SpeechToText(language=config.language)
    speak(GREETING)
    while True:
        try:
            input("[Press Enter and speak]")
        except EOFError:
            return
        print("Listening...", flush=True)
        text = _listen(stt, speak, timeout=6)
        if text is None:
            print("(didn't catch that)")
            continue
        print(f"You: {text}")
        reply = assistant.respond(text)
        if reply is None:
            continue
        speak(reply.text)
        if reply.exit:
            return


def run_wake_word(assistant: Assistant, speak: Callable[[str], None], config: Config) -> None:
    from jarvis.audio.stt import SpeechToText

    stt = SpeechToText(language=config.language)
    detector = WakeWordDetector(config.wake_words)
    speak(f"{GREETING} Say {config.wake_words[0].title()} to wake me.")
    while True:
        heard = _listen(stt, speak, timeout=None, phrase_time_limit=8)
        command = detector.extract(heard)
        if command is None:
            continue
        if not command:
            speak("Yes?")
            command = _listen(stt, speak, timeout=6)
            if command is None:
                continue
        print(f"You: {command}")
        reply = assistant.respond(command)
        if reply is None:
            continue
        speak(reply.text)
        if reply.exit:
            return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jarvis", description="JARVIS, a Claude-powered voice assistant.")
    parser.add_argument("--mode", choices=MODES, help="wake (wake word), ptt (push-to-talk) or text (keyboard)")
    parser.add_argument("--speak", action="store_true", help="in text mode, also speak replies aloud")
    parser.add_argument("--mute", action="store_true", help="print replies instead of speaking them")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    try:
        config = Config.from_env()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 2
    if not config.api_key:
        print("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        return 2

    from jarvis.brain import Brain
    from jarvis.skills import default_skills

    assistant = Assistant(Brain.from_config(config), default_skills(config.search_url))
    mode = args.mode or config.mode
    speak = _speaker(enabled=(args.speak or mode != "text") and not args.mute, config=config)

    try:
        if mode == "text":
            run_text(assistant, speak)
        elif mode == "ptt":
            run_push_to_talk(assistant, speak, config)
        else:
            run_wake_word(assistant, speak, config)
    except KeyboardInterrupt:
        print("\nGoodbye.")
    return 0
