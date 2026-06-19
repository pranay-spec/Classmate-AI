"""Quiz scoring and display helpers."""

from typing import Any


def score_quiz(
    quiz_data: dict[str, Any],
    user_answers: dict[int, str],
) -> dict[str, Any]:
    questions = quiz_data.get("questions", [])
    total = len(questions)
    correct_count = 0
    results = []

    for i, question in enumerate(questions):
        correct = str(question.get("correct", "")).upper()
        user = str(user_answers.get(i, "")).upper()
        is_correct = user == correct and user != ""
        if is_correct:
            correct_count += 1
        results.append(
            {
                "index": i,
                "question": question.get("question", ""),
                "options": question.get("options", {}),
                "user_answer": user,
                "correct_answer": correct,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
            }
        )

    percentage = round((correct_count / total) * 100) if total else 0
    message = _score_message(percentage, total, correct_count)

    return {
        "total": total,
        "correct": correct_count,
        "percentage": percentage,
        "results": results,
        "message": message,
    }


def _score_message(percentage: int, total: int, correct: int) -> str:
    if percentage == 100:
        return f"Shabash! Perfect score — {correct}/{total}! 🌟"
    if percentage >= 75:
        return f"Bahut accha! {correct}/{total} sahi — keep it up! 👏"
    if percentage >= 50:
        return f"Achha try! {correct}/{total} sahi — thoda aur practice karo. 💪"
    return f"Koi baat nahi! {correct}/{total} sahi — dubara try karo, seekhoge! 📚"


def format_question_for_tts(question: dict[str, Any], index: int) -> str:
    options = question.get("options", {})
    parts = [f"Question {index + 1}. {question.get('question', '')}"]
    for key in ["A", "B", "C", "D"]:
        if key in options:
            parts.append(f"Option {key}: {options[key]}")
    return ". ".join(parts)
