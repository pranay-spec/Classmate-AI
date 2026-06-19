"""Text-to-speech utilities using gTTS."""

import io
from typing import Optional

from gtts import gTTS


def text_to_speech_bytes(
    text: str,
    language_mode: str = "hinglish",
    slow: bool = False,
) -> Optional[bytes]:
    """Convert text to MP3 audio bytes for Streamlit playback."""
    if not text or not text.strip():
        return None

    lang = _resolve_gtts_lang(language_mode)
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.read()
    except Exception:
        if lang != "en":
            try:
                tts = gTTS(text=text, lang="en", slow=slow)
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                buffer.seek(0)
                return buffer.read()
            except Exception:
                return None
        return None


def _resolve_gtts_lang(language_mode: str) -> str:
    mapping = {
        "hindi": "hi",
        "english": "en",
        "hinglish": "hi",
    }
    return mapping.get(language_mode, "hi")


def build_explanation_narration(data: dict) -> str:
    """Combine title, explanation, and encouragement for student listen-aloud."""
    parts = []
    if data.get("title"):
        parts.append(str(data["title"]))
    if data.get("explanation"):
        parts.append(str(data["explanation"]))
    if data.get("encouragement"):
        parts.append(str(data["encouragement"]))
    return ". ".join(p.strip() for p in parts if p and p.strip())
