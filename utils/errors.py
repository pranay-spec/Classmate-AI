"""User-friendly error messages for the classroom UI."""


def format_api_error(exc: BaseException) -> str:
    """Convert API/technical errors into teacher-friendly Hinglish messages."""
    msg = str(exc).lower()
    if any(x in msg for x in ("503", "unavailable", "high demand", "overloaded")):
        return (
            "AI server abhi bahut busy hai (503). Yeh temporary hota hai - "
            "1-2 minute wait karke dubara try kijiye."
        )
    if any(x in msg for x in ("429", "rate limit", "resource exhausted", "quota")):
        return "API limit reach ho gayi (429). Thodi der wait karke phir try kijiye."
    if any(x in msg for x in ("401", "403", "api key", "invalid")):
        return "API key sahi nahi lag rahi. `.env` mein `GEMINI_API_KEY` check kijiye."
    if "timeout" in msg or "deadline" in msg:
        return "Request time out ho gayi. Internet check karke dubara try kijiye."
    return f"Kuch galat ho gaya: {exc}"
