"""Visual rendering helpers for smart board and diagrams."""

import html
from typing import Any


def render_key_points_html(points: list[str], smart_board: bool = False) -> str:
    font_size = "1.6rem" if smart_board else "1.1rem"
    items = "".join(
        f'<li style="margin-bottom:0.6rem;font-size:{font_size};">{html.escape(p)}</li>'
        for p in points
    )
    return f"""
    <div class="key-points-box">
        <h3 style="color:#1a5276;margin-bottom:0.8rem;">📌 Key Points</h3>
        <ul style="line-height:1.8;padding-left:1.2rem;">{items}</ul>
    </div>
    """


def render_diagram_html(diagram_text: str, smart_board: bool = False) -> str:
    lines = [line.strip() for line in diagram_text.strip().split("\n") if line.strip()]
    font_size = "1.8rem" if smart_board else "1.2rem"
    arrow_size = "2rem" if smart_board else "1.4rem"

    parts = []
    for line in lines:
        escaped = html.escape(line)
        if line in ("↓", "->", "→", "⬇"):
            parts.append(
                f'<div style="text-align:center;font-size:{arrow_size};color:#2874a6;margin:0.3rem 0;">↓</div>'
            )
        else:
            parts.append(
                f'<div class="diagram-node" style="font-size:{font_size};">{escaped}</div>'
            )

    nodes = "\n".join(parts)
    return f"""
    <div class="diagram-box" style="text-align:center;padding:1.5rem;">
        {nodes}
    </div>
    """


def render_explanation_card(
    data: dict[str, Any],
    smart_board: bool = False,
) -> str:
    title_size = "2.4rem" if smart_board else "1.6rem"
    body_size = "1.5rem" if smart_board else "1.05rem"

    title = html.escape(data.get("title", "Explanation"))
    explanation = html.escape(data.get("explanation", "")).replace("\n", "<br>")
    encouragement = html.escape(data.get("encouragement", ""))
    visual = html.escape(data.get("visual_summary", ""))

    return f"""
    <div class="explanation-card">
        <h2 style="color:#1a5276;font-size:{title_size};margin-bottom:1rem;">{title}</h2>
        <p style="font-size:{body_size};line-height:1.8;color:#2c3e50;">{explanation}</p>
        {f'<p style="font-style:italic;color:#566573;margin-top:1rem;font-size:{body_size};">🎯 Smart Board: {visual}</p>' if visual else ''}
        {f'<p style="color:#1e8449;font-size:{body_size};margin-top:1rem;font-weight:600;">{encouragement}</p>' if encouragement else ''}
    </div>
    """


def get_smart_board_css() -> str:
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Noto Sans Devanagari', sans-serif !important;
        }

        .main-header {
            background: linear-gradient(135deg, #1a5276 0%, #2874a6 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .main-header h1 { color: white !important; margin: 0; }
        .main-header p { color: #d6eaf8; margin: 0.5rem 0 0 0; }

        .key-points-box {
            background: #eaf2f8;
            border-left: 5px solid #2874a6;
            padding: 1.2rem 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
        }

        .diagram-box {
            background: #fdfefe;
            border: 2px solid #2874a6;
            border-radius: 12px;
            margin: 1rem 0;
        }

        .diagram-node {
            background: #d6eaf8;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            margin: 0.2rem auto;
            max-width: 400px;
            font-weight: 600;
            color: #1a5276;
        }

        .explanation-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin: 1rem 0;
        }

        .listen-audio-box {
            background: linear-gradient(135deg, #e8f8f5, #d1f2eb);
            border: 2px solid #1abc9c;
            border-radius: 12px;
            padding: 0.8rem 1.2rem;
            margin: 0.5rem 0 1rem 0;
            color: #117a65;
        }

        .listen-audio-box p {
            margin: 0;
            font-size: 1.05rem;
        }

        .stat-card {
            background: linear-gradient(135deg, #eaf2f8, #d6eaf8);
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            border: 1px solid #aed6f1;
        }

        .stat-number {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1a5276;
        }

        .voice-btn label {
            font-size: 1.1rem !important;
        }

        div[data-testid="stSidebar"] {
            background-color: #f4f9fd;
        }

        /* Smart Board Mode */
        .smart-board-mode .main-header h1 { font-size: 3rem !important; }
        .smart-board-mode .explanation-card { font-size: 1.4rem; }
        .smart-board-mode .key-points-box { font-size: 1.3rem; }
        .smart-board-mode .diagram-node { font-size: 1.6rem !important; padding: 1rem 1.5rem; }

        /* Hide sidebar in smart board */
        .smart-board-mode div[data-testid="stSidebar"] { display: none; }

        /* Large accessible buttons */
        .stButton > button {
            min-height: 3rem;
            font-size: 1.05rem;
            border-radius: 10px;
        }

        .quiz-correct {
            background-color: #d5f5e3 !important;
            border: 2px solid #27ae60 !important;
            border-radius: 8px;
            padding: 0.5rem;
        }

        .quiz-wrong {
            background-color: #fadbd8 !important;
            border: 2px solid #e74c3c !important;
            border-radius: 8px;
            padding: 0.5rem;
        }
    </style>
    """


def get_score_badge_html(percentage: int, message: str) -> str:
    color = "#27ae60" if percentage >= 75 else "#f39c12" if percentage >= 50 else "#e74c3c"
    return f"""
    <div style="text-align:center;padding:2rem;background:{color}22;border-radius:12px;border:2px solid {color};">
        <div style="font-size:3rem;font-weight:700;color:{color};">{percentage}%</div>
        <div style="font-size:1.3rem;margin-top:0.5rem;color:#2c3e50;">{html.escape(message)}</div>
    </div>
    """
