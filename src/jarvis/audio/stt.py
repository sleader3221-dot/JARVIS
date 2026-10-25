"""Speech-to-text from the default microphone using the SpeechRecognition package."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class SpeechServiceError(RuntimeError):
    """The speech recognition service could not be reached."""


class SpeechToText:
    def __init__(self, language: str = "en-US", pause_threshold: float = 0.8) -> None:
        import speech_recognition as sr  # needs SpeechRecognition + PyAudio

        self._sr = sr
        self.language = language
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        with self.microphone as source:
            log.info("Calibrating for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen(self, timeout: float | None = None, phrase_time_limit: float | None = 15) -> str | None:
        """Record one phrase and transcribe it. Returns None on silence or unintelligible audio.

        `timeout` is how long to wait for speech to start (None waits forever).
        """
        sr = self._sr
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except sr.WaitTimeoutError:
                return None
        try:
            # Google's free Web Speech endpoint: no key required, needs internet.
            text = self.recognizer.recognize_google(audio, language=self.language)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            raise SpeechServiceError(f"Speech recognition service unavailable: {e}") from e
        log.debug("Heard: %s", text)
        return text
