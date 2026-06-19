"""Gemini 2.5 Flash integration for ClassMate AI."""

import json
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from utils.prompts import (
    build_explanation_prompt,
    build_quiz_prompt,
    build_topic_extraction_prompt,
)

load_dotenv()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]
# Deduplicate while preserving order
FALLBACK_MODELS = list(dict.fromkeys(FALLBACK_MODELS))

MAX_RETRIES = 4
BASE_RETRY_DELAY_SEC = 2


def _get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key or key == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to your .env file. "
            "Get a key at https://aistudio.google.com/apikey"
        )
    return key


def _get_client() -> genai.Client:
    return genai.Client(api_key=_get_api_key())


def _is_retryable_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    retry_markers = (
        "503",
        "429",
        "500",
        "502",
        "504",
        "unavailable",
        "overloaded",
        "high demand",
        "rate limit",
        "resource exhausted",
        "deadline",
        "timeout",
    )
    return any(marker in msg for marker in retry_markers)


def _generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    client = _get_client()
    last_error: BaseException | None = None

    for model in FALLBACK_MODELS:
        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                text = response.text or ""
                if text.strip():
                    return text
                raise ValueError("Empty response from AI model")
            except Exception as exc:
                last_error = exc
                if _is_retryable_error(exc) and attempt < MAX_RETRIES - 1:
                    time.sleep(BASE_RETRY_DELAY_SEC * (2**attempt))
                    continue
                if _is_retryable_error(exc):
                    break
                raise

    if last_error:
        raise last_error
    raise RuntimeError("AI service unavailable. Please try again later.")


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse AI response as JSON: {text[:200]}...")


def generate_explanation(
    topic: str,
    class_level: int,
    language: str,
) -> dict[str, Any]:
    prompt = build_explanation_prompt(topic, class_level, language)
    text = _generate(prompt, temperature=0.7, max_tokens=2048)
    return _parse_json_response(text)


def generate_quiz(
    topic: str,
    class_level: int,
    language: str,
    num_questions: int = 4,
) -> dict[str, Any]:
    prompt = build_quiz_prompt(topic, class_level, language, num_questions)
    text = _generate(prompt, temperature=0.6, max_tokens=3000)
    return _parse_json_response(text)


def extract_intent_from_transcript(
    transcript: str,
    default_class_level: int,
) -> dict[str, Any]:
    prompt = build_topic_extraction_prompt(transcript, default_class_level)
    text = _generate(prompt, temperature=0.2, max_tokens=512)
    return _parse_json_response(text)
