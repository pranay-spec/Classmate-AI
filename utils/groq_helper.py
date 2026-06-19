"""Groq LLM integration for ClassMate AI (replaces Gemini)."""

import json
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from utils.prompts import (
    build_explanation_prompt,
    build_quiz_prompt,
    build_topic_extraction_prompt,
)

load_dotenv()

PRIMARY_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]
# Deduplicate while preserving order
FALLBACK_MODELS = list(dict.fromkeys(FALLBACK_MODELS))

MAX_RETRIES = 3
BASE_RETRY_DELAY_SEC = 1


def _get_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file. "
            "Get a free key at https://console.groq.com/keys"
        )
    return key


def _get_client() -> Groq:
    return Groq(api_key=_get_api_key())


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
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                text = response.choices[0].message.content or ""
                if text.strip():
                    return text
                raise ValueError("Empty response from AI model")
            except Exception as exc:
                last_error = exc
                if _is_retryable_error(exc) and attempt < MAX_RETRIES - 1:
                    time.sleep(BASE_RETRY_DELAY_SEC * (2**attempt))
                    continue
                if _is_retryable_error(exc):
                    break  # Try next model
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
