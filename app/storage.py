import os
import sqlite3
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "tasks.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    # Allows accessing columns by name (row["title"]) instead of index (row[1])
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Creates the tasks table if it does not already exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN NOT NULL DEFAULT 0
            )
        """)


def fetch_all_tasks() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, description, completed FROM tasks"
        ).fetchall()
        return [{**dict(row), "completed": bool(row["completed"])} for row in rows]


def fetch_task_by_id(task_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, description, completed FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if not row:
            return None
        return {**dict(row), "completed": bool(row["completed"])}


def insert_task(title: str, description: Optional[str], completed: bool) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, completed) VALUES (?, ?, ?)",
            (title, description, int(completed)),
        )
        new_id = cursor.lastrowid
    return fetch_task_by_id(new_id)


def update_task_by_id(
    task_id: int, title: str, description: Optional[str], completed: bool
) -> Optional[dict]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, completed = ?
            WHERE id = ?
            """,
            (title, description, int(completed), task_id),
        )
        if cursor.rowcount == 0:
            return None
    return fetch_task_by_id(task_id)


def delete_task_by_id(task_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0
