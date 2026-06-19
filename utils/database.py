"""SQLite database for teacher dashboard and activity logging."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "data/classmate.db")


def _ensure_db_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    _ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                topic TEXT,
                class_level INTEGER,
                language TEXT,
                details TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                explanations_count INTEGER DEFAULT 0,
                quizzes_count INTEGER DEFAULT 0
            );

            INSERT OR IGNORE INTO stats (id, explanations_count, quizzes_count)
            VALUES (1, 0, 0);
            """
        )
        conn.commit()
    finally:
        conn.close()


def log_activity(
    activity_type: str,
    topic: str = "",
    class_level: int = 5,
    language: str = "hinglish",
    details: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO activities (activity_type, topic, class_level, language, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                activity_type,
                topic,
                class_level,
                language,
                details,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        column = "explanations_count" if activity_type == "explanation" else "quizzes_count"
        conn.execute(
            f"UPDATE stats SET {column} = {column} + 1 WHERE id = 1"
        )
        conn.commit()
    finally:
        conn.close()


def get_dashboard_data(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        stats_row = conn.execute(
            "SELECT explanations_count, quizzes_count FROM stats WHERE id = 1"
        ).fetchone()
        recent = conn.execute(
            """
            SELECT activity_type, topic, class_level, language, created_at
            FROM activities
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()
        topics = conn.execute(
            """
            SELECT topic, COUNT(*) as count
            FROM activities
            WHERE topic IS NOT NULL AND topic != ''
            GROUP BY topic
            ORDER BY count DESC
            LIMIT 5
            """
        ).fetchall()

        return {
            "explanations_count": stats_row["explanations_count"] if stats_row else 0,
            "quizzes_count": stats_row["quizzes_count"] if stats_row else 0,
            "recent_activities": [dict(row) for row in recent],
            "top_topics": [dict(row) for row in topics],
        }
    finally:
        conn.close()
