# JARVIS

A personal AI voice assistant in Python. Say "Jarvis" (or press Enter) and ask a question. JARVIS transcribes what you said, handles simple commands itself, sends everything else to Claude, and reads the reply aloud.

## Features

- **Three ways to start listening:** a wake word (`wake`, the default), push-to-talk with Enter (`ptt`), or typing (`text`).
- **Speech-to-text** with [SpeechRecognition](https://pypi.org/project/SpeechRecognition/), using Google's free Web Speech service.
- **Claude** (`claude-opus-5-5` by default) through the official `anthropic` SDK. JARVIS remembers your last 10 exchanges, can search the web to answer questions about current events, and if Claude's safety filter declines a request, the API retries it on a fallback model (server-side fallback).
- **Text-to-speech** with [pyttsx3](https://pypi.org/project/pyttsx3/). On Windows this uses the built-in SAPI5 voices and works offline.
- **Built-in skills** that run locally, without calling Claude:
  - Time and date: "what time is it?", "what's the date?"
  - Opening websites: "open YouTube", "go to github", "open example dot com"
  - Web search in your browser: "search for pizza near me", "google python decorators", "look up …"
- **Voice commands:** "clear memory" starts a new conversation; "goodbye" exits.

## Setup on Windows

You need Windows 10 or 11, Python 3.10 to 3.13 ([python.org](https://www.python.org/downloads/), with **"Add python.exe to PATH"** ticked), a microphone, and a Claude API key from the [Claude Console](https://platform.claude.com/).

Open **PowerShell** in the project folder:

```powershell
# 1. Create and activate a virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1
# If activation is blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 2. Install dependencies, then the package itself
pip install -r requirements.txt
pip install -e .

# 3. Configure your API key
copy .env.example .env
notepad .env        # set ANTHROPIC_API_KEY=sk-ant-...
```

Instead of using `.env`, you can set the key for the current session with `$env:ANTHROPIC_API_KEY = "sk-ant-..."`.

**Microphone access:** open Settings, then Privacy & security, then Microphone, and allow desktop apps to use the microphone.

## Running

```powershell
python -m jarvis                 # wake word mode: say "Jarvis, what's the weather in Paris?"
python -m jarvis --mode ptt      # press Enter, then speak
python -m jarvis --mode text     # type instead of speaking (no microphone needed)
python -m jarvis --mode text --speak   # type, and hear the replies spoken
python -m jarvis --mute          # use voice input, but print replies instead of speaking them
python -m jarvis -v              # debug logging
```

After `pip install -e .`, the `jarvis` command does the same thing as `python -m jarvis`. Press Ctrl+C to quit at any time.

**Try text mode first** (`--mode text`). It checks your API key and Claude connection without any audio setup.

In wake word mode you can say the wake word and your request together ("Jarvis, open YouTube"), or say "Jarvis", wait for "Yes?", and then speak.

## Configuration

All settings are environment variables and can go in `.env`. See [.env.example](.env.example) for the full list.

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your Claude API key |
| `JARVIS_MODEL` | `claude-opus-5-5` | Claude model |
| `JARVIS_EFFORT` | `low` | Effort level: `low` to `max`. Higher is more thorough but slower |
| `JARVIS_MEMORY_TURNS` | `10` | How many recent exchanges to remember |
| `JARVIS_WEB_SEARCH` | `true` | Let Claude search the web while answering |
| `JARVIS_MODE` | `wake` | `wake`, `ptt` or `text` |
| `JARVIS_WAKE_WORDS` | `jarvis,jervis` | Wake words, comma-separated |
| `JARVIS_LANGUAGE` | `en-US` | Speech recognition language |
| `JARVIS_TTS_RATE` / `JARVIS_TTS_VOICE` | `185` / system default | Speaking rate, and part of a voice name such as `Zira` |
| `JARVIS_SEARCH_URL` | Google | Search URL, with `{query}` where the search terms go |

## Project layout

```
src/jarvis/
  cli.py           entry point and the listen → think → speak loops
  config.py        settings loaded from environment variables
  assistant.py     routing: built-in commands, then skills, then Claude
  brain.py         Claude API client, system prompt, error handling
  memory.py        rolling short-term conversation memory
  wake.py          wake word detection on transcripts
  audio/stt.py     microphone capture and speech recognition
  audio/tts.py     speech output and markdown clean-up
  skills/          time/date, websites, web search
tests/             unit tests for everything except audio
```

To add a skill, write a class with a `name` and a `handle(text) -> str | None` method. It returns the reply, or `None` to pass the request on. Then register it in `skills/__init__.py:default_skills`.

## Tests

```powershell
python -m pytest
```

The tests cover config, memory, wake word parsing, skills, request routing and the Claude client logic, using a fake API client. They don't call the API or use audio devices. They also run with the standard library alone (`python -m unittest discover -s tests -t .`).

## Troubleshooting

- **`pip install PyAudio` fails:** PyAudio publishes prebuilt Windows wheels for Python 3.8 to 3.13. On a newer Python, install 3.13 and recreate the virtual environment with `py -3.13 -m venv .venv`.
- **"didn't catch that" or no response:** check the Windows input device and microphone permissions. Speak after "Listening..." appears; JARVIS calibrates for background noise when it starts.
- **"speech recognition service is unavailable":** recognition uses Google's online service, so you need an internet connection.
- **"couldn't sign in to the Claude API":** check `ANTHROPIC_API_KEY` in `.env`.
- **The wake word isn't recognized:** add the word the recognizer actually hears (run with `-v` to see transcripts) to `JARVIS_WAKE_WORDS`, or use `--mode ptt`.
