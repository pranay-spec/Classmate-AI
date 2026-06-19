"""
ClassMate AI — Voice-driven classroom co-pilot for government school teachers.
Connecting Dreams Foundation — Round 2 Technical Assignment
"""

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from utils.database import get_dashboard_data, init_db, log_activity
from utils.errors import format_api_error
from utils.gemini_helper import (
    extract_intent_from_transcript,
    generate_explanation,
    generate_quiz,
)
from utils.quiz import format_question_for_tts, score_quiz
from utils.speech import get_language_code, parse_voice_command, transcribe_audio_bytes
from utils.tts import build_explanation_narration, text_to_speech_bytes
from utils.visuals import (
    get_score_badge_html,
    get_smart_board_css,
    render_diagram_html,
    render_explanation_card,
    render_key_points_html,
)

load_dotenv()

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClassMate AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Defaults ───────────────────────────────────────────────────
DEFAULTS = {
    "transcript": "",
    "explanation_data": None,
    "quiz_data": None,
    "quiz_answers": {},
    "quiz_submitted": False,
    "quiz_score": None,
    "last_topic": "",
    "explanation_audio_bytes": None,
    "explanation_audio_key": None,
    "smart_board": False,
    "language": os.getenv("DEFAULT_LANGUAGE", "hinglish"),
    "class_level": int(os.getenv("DEFAULT_CLASS_LEVEL", "5")),
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

init_db()


# ── Helpers ──────────────────────────────────────────────────────────────────
def apply_smart_board_class():
    if st.session_state.smart_board:
        st.markdown('<div class="smart-board-mode">', unsafe_allow_html=True)


def render_header():
    st.markdown(get_smart_board_css(), unsafe_allow_html=True)
    st.markdown(
        """
        <div class="main-header">
            <h1>📚 ClassMate AI</h1>
            <p>Hands-free AI Classroom Co-pilot for Government School Teachers</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_controls():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/classroom.png", width=80)
        st.markdown("### ⚙️ Classroom Settings")

        st.session_state.language = st.selectbox(
            "🌐 Language Mode",
            options=["hinglish", "hindi", "english"],
            index=["hinglish", "hindi", "english"].index(st.session_state.language),
            help="Hinglish is recommended for Haryana classrooms",
        )

        st.session_state.class_level = st.selectbox(
            "🎓 Class Level",
            options=list(range(1, 11)),
            index=st.session_state.class_level - 1,
            format_func=lambda x: f"Class {x}",
        )

        st.session_state.smart_board = st.toggle(
            "🖥️ Smart Board Mode",
            value=st.session_state.smart_board,
            help="Fullscreen-friendly view with large fonts and high contrast",
        )

        st.divider()
        st.markdown("### 💡 Quick Commands")
        st.markdown(
            """
            **Explain:**
            - *"Explain photosynthesis for class 5"*
            - *"Explain water cycle for class 6"*

            **Quiz:**
            - *"Create a quiz"*
            - *"Quiz me on fractions"*
            """
        )

        api_configured = bool(
            os.getenv("GEMINI_API_KEY")
            and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here"
        )
        if api_configured:
            st.success("✅ Gemini API connected")
        else:
            st.error("❌ Add GEMINI_API_KEY to .env")


def process_transcript(transcript: str):
    """Route transcript to explanation or quiz based on intent."""
    if not transcript.strip():
        st.warning("Kuch sunai nahi diya. Please try again or type your command.")
        return

    st.session_state.transcript = transcript

    with st.spinner("Samajh raha hoon... Understanding your command..."):
        try:
            intent_data = extract_intent_from_transcript(
                transcript, st.session_state.class_level
            )
        except Exception:
            intent_data = parse_voice_command(transcript)

    intent = intent_data.get("intent", "explain")
    topic = intent_data.get("topic", transcript)
    class_level = intent_data.get("class_level") or st.session_state.class_level

    if isinstance(class_level, str) and class_level.isdigit():
        class_level = int(class_level)
    elif not isinstance(class_level, int):
        class_level = st.session_state.class_level

    st.session_state.last_topic = topic

    if intent == "quiz":
        generate_quiz_flow(topic, class_level)
    else:
        generate_explanation_flow(topic, class_level)


def generate_explanation_flow(topic: str, class_level: int):
    with st.spinner(f"Class {class_level} ke liye explanation bana raha hoon..."):
        try:
            data = generate_explanation(
                topic, class_level, st.session_state.language
            )
            st.session_state.explanation_data = data
            st.session_state.explanation_audio_bytes = None
            st.session_state.explanation_audio_key = None
            st.session_state.quiz_data = None
            st.session_state.quiz_submitted = False
            log_activity(
                "explanation",
                topic=topic,
                class_level=class_level,
                language=st.session_state.language,
                details=data.get("title", ""),
            )
            st.success(f"✅ Explanation ready: **{data.get('title', topic)}**")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(format_api_error(exc))


def generate_quiz_flow(topic: str, class_level: int):
    if not topic or topic.lower() in ("general science", "create a quiz"):
        topic = st.session_state.last_topic or "general science"

    with st.spinner(f"Class {class_level} ke liye quiz bana raha hoon..."):
        try:
            data = generate_quiz(
                topic, class_level, st.session_state.language, num_questions=4
            )
            st.session_state.quiz_data = data
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score = None
            log_activity(
                "quiz",
                topic=topic,
                class_level=class_level,
                language=st.session_state.language,
                details=data.get("quiz_title", ""),
            )
            st.success(f"✅ Quiz ready: **{data.get('quiz_title', topic)}**")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(format_api_error(exc))


def render_voice_input_section():
    st.markdown("## 🎤 Teaching Assistant")
    st.caption("Boliye ya type kijiye — microphone se ya neeche text box se")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 🎙️ Voice Input")
        audio_data = st.audio_input(
            "Record your command",
            key="voice_input",
            help="Press to record: 'Explain photosynthesis for class 5' or 'Create a quiz'",
        )

        if audio_data is not None:
            if st.button("🔊 Transcribe & Process", type="primary", use_container_width=True):
                with st.spinner("Sun raha hoon... Listening..."):
                    transcript, source = transcribe_audio_bytes(
                        audio_data.getvalue(),
                        get_language_code(st.session_state.language),
                    )
                if transcript and source not in ("empty", "unrecognized", "error"):
                    process_transcript(transcript)
                elif source == "unrecognized":
                    st.warning("Audio clear nahi tha. Please speak clearly or use text input.")
                else:
                    st.error(transcript or "Could not transcribe audio.")

    with col2:
        st.markdown("#### ⌨️ Text Input (Backup)")
        text_command = st.text_area(
            "Type your command",
            placeholder='e.g. "Explain water cycle for class 6" or "Quiz me on photosynthesis"',
            height=100,
            label_visibility="collapsed",
        )
        if st.button("▶️ Process Command", use_container_width=True):
            process_transcript(text_command)

    if st.session_state.transcript:
        st.info(f"📝 **Transcript:** {st.session_state.transcript}")


def _explanation_audio_cache_key(data: dict[str, Any]) -> str:
    return f"{data.get('title', '')}|{data.get('explanation', '')}"


def prepare_explanation_audio(data: dict[str, Any]) -> bytes | None:
    """Generate or return cached TTS audio for the full explanation."""
    cache_key = _explanation_audio_cache_key(data)
    if (
        st.session_state.explanation_audio_key == cache_key
        and st.session_state.explanation_audio_bytes
    ):
        return st.session_state.explanation_audio_bytes

    narration = build_explanation_narration(data)
    if not narration:
        return None

    audio_bytes = text_to_speech_bytes(
        narration, st.session_state.language, slow=True
    )
    if audio_bytes:
        st.session_state.explanation_audio_bytes = audio_bytes
        st.session_state.explanation_audio_key = cache_key
    return audio_bytes


def render_explanation_section():
    data: dict[str, Any] | None = st.session_state.explanation_data
    if not data:
        return

    st.markdown("---")
    smart = st.session_state.smart_board

    header_col, listen_col = st.columns([4, 1] if not smart else [3, 2])
    with header_col:
        st.markdown("## 📖 Explanation")
        st.caption("Students explanation padh sakte hain ya neeche **Suniye** button se sun sakte hain")
    with listen_col:
        listen_label = "🔊 Suniye" if not smart else "🔊 Suniye — Listen"
        listen = st.button(
            listen_label,
            type="primary",
            use_container_width=True,
            key="listen_explanation",
            help="Poori explanation sunne ke liye dabayein",
        )

    if listen:
        with st.spinner("Audio tayyar ho rahi hai... Students sun sakte hain"):
            audio_bytes = prepare_explanation_audio(data)
        if not audio_bytes:
            st.warning("Audio generate nahi ho paya. Internet check kijiye.")

    if st.session_state.explanation_audio_bytes:
        st.markdown(
            '<div class="listen-audio-box">'
            '<p><strong>🎧 Students ke liye</strong> — play button dabakar explanation suniye</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.audio(st.session_state.explanation_audio_bytes, format="audio/mp3")

    st.markdown(render_explanation_card(data, smart), unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        points = data.get("key_points", [])
        if points:
            st.markdown(
                render_key_points_html(points, smart), unsafe_allow_html=True
            )

    with col_b:
        diagram = data.get("diagram", "")
        if diagram:
            st.markdown("### 📊 Text Diagram")
            st.markdown(render_diagram_html(diagram, smart), unsafe_allow_html=True)


def render_quiz_section():
    data: dict[str, Any] | None = st.session_state.quiz_data
    if not data:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("## ❓ Quiz Section")
            if st.button(
                "🎯 Generate Quiz on Last Topic",
                type="primary",
                use_container_width=True,
                disabled=not st.session_state.last_topic,
            ):
                generate_quiz_flow(
                    st.session_state.last_topic, st.session_state.class_level
                )
        return

    st.markdown("---")
    st.markdown(f"## ❓ {data.get('quiz_title', 'Classroom Quiz')}")
    st.caption(f"Topic: {data.get('topic', '')} | Class {st.session_state.class_level}")

    questions = data.get("questions", [])

    if st.button("🔊 Read All Questions Aloud", key="read_quiz"):
        full_text = " ".join(
            format_question_for_tts(q, i) for i, q in enumerate(questions)
        )
        with st.spinner("Preparing quiz audio..."):
            audio_bytes = text_to_speech_bytes(
                full_text, st.session_state.language, slow=True
            )
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")

    for i, question in enumerate(questions):
        st.markdown(f"**Q{i + 1}. {question.get('question', '')}**")
        options = question.get("options", {})
        option_keys = ["A", "B", "C", "D"]

        if st.session_state.quiz_submitted and st.session_state.quiz_score:
            result = st.session_state.quiz_score["results"][i]
            for key in option_keys:
                if key not in options:
                    continue
                label = f"{key}. {options[key]}"
                if key == result["correct_answer"]:
                    st.markdown(f'<div class="quiz-correct">✅ {label}</div>', unsafe_allow_html=True)
                elif key == result["user_answer"] and not result["is_correct"]:
                    st.markdown(f'<div class="quiz-wrong">❌ {label}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(label)
            if result.get("explanation"):
                st.caption(f"💡 {result['explanation']}")
        else:
            choice = st.radio(
                f"Answer for Q{i + 1}",
                options=option_keys,
                format_func=lambda k, opts=options: f"{k}. {opts.get(k, '')}",
                key=f"quiz_q_{i}",
                label_visibility="collapsed",
            )
            st.session_state.quiz_answers[i] = choice

        st.divider()

    if not st.session_state.quiz_submitted:
        if st.button("✅ Submit Answers", type="primary", use_container_width=True):
            score = score_quiz(data, st.session_state.quiz_answers)
            st.session_state.quiz_score = score
            st.session_state.quiz_submitted = True
            st.rerun()
    else:
        score = st.session_state.quiz_score
        if score:
            st.markdown(
                get_score_badge_html(score["percentage"], score["message"]),
                unsafe_allow_html=True,
            )
            st.markdown(
                f"### Score: **{score['correct']}/{score['total']}** correct"
            )
        if st.button("🔄 New Quiz", use_container_width=True):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score = None
            st.session_state.quiz_answers = {}
            generate_quiz_flow(
                st.session_state.last_topic or data.get("topic", ""),
                st.session_state.class_level,
            )


def render_dashboard():
    st.markdown("---")
    st.markdown("## 📊 Teacher Dashboard")

    dashboard = get_dashboard_data()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{dashboard["explanations_count"]}</div>'
            f'<div>Explanations Generated</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{dashboard["quizzes_count"]}</div>'
            f'<div>Quizzes Generated</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        top = dashboard["top_topics"][0]["topic"] if dashboard["top_topics"] else "—"
        st.markdown(
            f'<div class="stat-card"><div class="stat-number" style="font-size:1.4rem;">{top}</div>'
            f'<div>Most Asked Topic</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 📋 Recent Classroom Activities")
    if dashboard["recent_activities"]:
        for act in dashboard["recent_activities"]:
            icon = "📖" if act["activity_type"] == "explanation" else "❓"
            st.markdown(
                f"{icon} **{act['topic'] or 'General'}** — "
                f"Class {act['class_level']} | {act['language']} | "
                f"{act['created_at'][:16].replace('T', ' ')}"
            )
    else:
        st.info("Abhi koi activity nahi hai. Pehla explanation ya quiz generate kijiye!")


def render_quick_actions():
    """One-click demo buttons for evaluators."""
    st.markdown("### ⚡ Quick Demo (One-Click)")
    demos = [
        ("🌱 Explain Photosynthesis (Class 5)", "Explain photosynthesis for class 5"),
        ("💧 Explain Water Cycle (Class 6)", "Explain water cycle for class 6"),
        ("🔢 Explain Fractions (Class 3)", "Explain fractions for class 3"),
        ("❓ Quiz on Photosynthesis", "Quiz me on photosynthesis"),
    ]
    cols = st.columns(len(demos))
    for col, (label, command) in zip(cols, demos):
        with col:
            if st.button(label, use_container_width=True):
                process_transcript(command)


# ── Main App ─────────────────────────────────────────────────────────────────
def main():
    apply_smart_board_class()
    render_header()
    sidebar_controls()

    if st.session_state.smart_board:
        st.info("🖥️ **Smart Board Mode ON** — Large fonts, high contrast, projection-ready")

    render_quick_actions()
    render_voice_input_section()
    render_explanation_section()
    render_quiz_section()
    render_dashboard()

    st.markdown("---")
    st.caption(
        "ClassMate AI · Connecting Dreams Foundation · "
        "Built with ❤️ for Haryana government school teachers"
    )


if __name__ == "__main__":
    main()
