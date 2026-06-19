"""Speech-to-text utilities for ClassMate AI."""

import io
import tempfile
from typing import Optional

import speech_recognition as sr
from pydub import AudioSegment


def transcribe_audio_bytes(
    audio_bytes: bytes,
    language_hint: str = "hi-IN",
) -> tuple[str, str]:
    """
    Transcribe audio bytes to text.

    Returns (transcript, source) where source is 'google' or 'error'.
    Supports Hindi (hi-IN), English (en-IN), and Hinglish via Indian locale.
    """
    if not audio_bytes:
        return "", "empty"

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_segment.export(tmp.name, format="wav")
            wav_path = tmp.name

        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)

        locales = [language_hint, "en-IN", "hi-IN"]
        for locale in locales:
            try:
                text = recognizer.recognize_google(audio_data, language=locale)
                if text.strip():
                    return text.strip(), "google"
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                break

        return "", "unrecognized"

    except Exception as exc:
        return f"[Speech error: {exc}]", "error"


def parse_voice_command(transcript: str) -> dict:
    """Simple local parser as fallback when API is unavailable."""
    text = transcript.lower().strip()
    result = {"intent": "explain", "topic": "", "class_level": None}

    quiz_triggers = ["create a quiz", "quiz me", "start quiz", "quiz on", "quiz about"]
    explain_triggers = ["explain", "teach", "batao", "samjhao", "bataye"]

    for trigger in quiz_triggers:
        if trigger in text:
            result["intent"] = "quiz"
            if "quiz on" in text:
                result["topic"] = text.split("quiz on", 1)[-1].strip()
            elif "quiz about" in text:
                result["topic"] = text.split("quiz about", 1)[-1].strip()
            elif "quiz me on" in text:
                result["topic"] = text.split("quiz me on", 1)[-1].strip()
            break

    if result["intent"] == "explain":
        for trigger in explain_triggers:
            if trigger in text:
                parts = text.split(trigger, 1)
                if len(parts) > 1:
                    topic_part = parts[1].strip()
                    for prefix in ["for class", "class", "for"]:
                        if prefix in topic_part:
                            before, after = topic_part.split(prefix, 1)
                            result["topic"] = before.strip()
                            digits = "".join(c for c in after if c.isdigit())
                            if digits:
                                result["class_level"] = int(digits[0])
                            break
                    else:
                        result["topic"] = topic_part
                break

    if not result["topic"] and text:
        result["topic"] = text

    return result


def get_language_code(language_mode: str) -> str:
    mapping = {
        "hindi": "hi-IN",
        "english": "en-IN",
        "hinglish": "hi-IN",
    }
    return mapping.get(language_mode, "hi-IN")
