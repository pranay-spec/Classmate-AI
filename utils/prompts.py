"""Prompt templates for ClassMate AI teaching assistant."""

SYSTEM_PROMPT = """You are an AI Teaching Assistant helping government school teachers in India.

Rules:
1. Explain concepts in simple Hinglish.
2. Adapt to student grade level.
3. Use practical examples from daily life.
4. Keep responses concise.
5. Avoid technical jargon.
6. Encourage curiosity.
7. Generate educational diagrams when useful.
8. Always maintain educational accuracy."""

LANGUAGE_INSTRUCTIONS = {
    "hinglish": (
        "Use simple conversational Hinglish — mix Hindi and English naturally, "
        "the way teachers speak in Haryana classrooms. Example: 'Plants ko sunlight "
        "chahiye hoti hai taaki woh apna khana bana sakein.'"
    ),
    "hindi": (
        "Use simple Hindi (Devanagari script) suitable for government school students. "
        "Keep sentences short and clear."
    ),
    "english": (
        "Use simple English suitable for Indian government school students. "
        "Avoid complex vocabulary."
    ),
}

GRADE_COMPLEXITY = {
    1: "Use very simple words, 1-2 sentence explanations, lots of everyday examples like toys, home, family.",
    2: "Use very simple words, short sentences, examples from school and home life.",
    3: "Use simple language, short paragraphs, relatable examples from daily life.",
    4: "Use clear simple language with slightly more detail, school and village examples.",
    5: "Use age-appropriate language with clear structure, include one real-world application.",
    6: "Use structured explanations with cause-effect, include local Indian context examples.",
    7: "Use moderate detail, introduce basic scientific terms with simple definitions.",
    8: "Use more detailed explanations with proper terminology explained simply.",
    9: "Use detailed explanations suitable for board exam preparation basics.",
    10: "Use comprehensive explanations with proper terminology and deeper connections.",
}


def get_grade_instruction(class_level: int) -> str:
    level = max(1, min(10, class_level))
    return GRADE_COMPLEXITY.get(level, GRADE_COMPLEXITY[5])


def get_language_instruction(language: str) -> str:
    return LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["hinglish"])


def build_explanation_prompt(topic: str, class_level: int, language: str) -> str:
    return f"""{SYSTEM_PROMPT}

TASK: Generate a classroom-ready explanation for the smart board.

Topic: {topic}
Class Level: Class {class_level}
Language Mode: {language}

Grade Adaptation: {get_grade_instruction(class_level)}
Language Style: {get_language_instruction(language)}

Respond ONLY with valid JSON in this exact structure (no markdown fences):
{{
  "title": "Topic title in the chosen language",
  "explanation": "Full friendly teacher-style explanation (2-4 short paragraphs)",
  "key_points": ["point 1", "point 2", "point 3", "point 4"],
  "diagram": "Text-based diagram using arrows (↓) and newlines, e.g.:\\nSun\\n↓\\nEvaporation\\n↓\\nClouds",
  "visual_summary": "One sentence describing what to show on the smart board",
  "encouragement": "One encouraging line for students"
}}"""


def build_quiz_prompt(
    topic: str,
    class_level: int,
    language: str,
    num_questions: int = 4,
) -> str:
    return f"""{SYSTEM_PROMPT}

TASK: Create a classroom quiz for government school students.

Topic: {topic if topic else "recent classroom topic"}
Class Level: Class {class_level}
Language Mode: {language}
Number of Questions: {num_questions}

Grade Adaptation: {get_grade_instruction(class_level)}
Language Style: {get_language_instruction(language)}

Create {num_questions} multiple choice questions (4 options each: A, B, C, D).
Difficulty must match Class {class_level} level.

Respond ONLY with valid JSON (no markdown fences):
{{
  "quiz_title": "Quiz title",
  "topic": "topic name",
  "questions": [
    {{
      "question": "Question text",
      "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
      "correct": "A",
      "explanation": "Brief explanation why this is correct"
    }}
  ]
}}"""


def build_topic_extraction_prompt(transcript: str, class_level: int) -> str:
    return f"""Analyze this teacher voice command from an Indian classroom.

Transcript: "{transcript}"
Default Class Level: Class {class_level}

Determine the intent and extract details.

Respond ONLY with valid JSON (no markdown fences):
{{
  "intent": "explain" or "quiz",
  "topic": "extracted topic name",
  "class_level": {class_level},
  "confidence": "high" or "medium" or "low"
}}

Examples:
- "Explain photosynthesis for class 5" → intent: explain, topic: photosynthesis, class_level: 5
- "Quiz me on water cycle" → intent: quiz, topic: water cycle
- "Create a quiz" → intent: quiz, topic: use recent topic or "general science"
"""
