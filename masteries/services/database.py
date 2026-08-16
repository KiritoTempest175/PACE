import sqlite3
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("backend/pace.db")


def get_db_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        workspace TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        text TEXT NOT NULL,
        source TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()


def get_conversations():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, workspace, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "title": r["title"],
            "workspace": r["workspace"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return result


def get_conversation(conversation_id: str):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, title, workspace, created_at, updated_at FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    conv_row = cursor.fetchone()
    if not conv_row:
        conn.close()
        return None

    cursor.execute(
        "SELECT id, role, text, source, status, created_at FROM messages WHERE conversation_id = ? ORDER BY datetime(created_at) ASC",
        (conversation_id,)
    )
    msg_rows = cursor.fetchall()
    conn.close()

    messages = [
        {
            "id": m["id"],
            "role": m["role"],
            "text": m["text"],
            "source": m["source"],
            "status": m["status"],
            "created_at": m["created_at"]
        }
        for m in msg_rows
    ]

    return {
        "id": conv_row["id"],
        "title": conv_row["title"],
        "workspace": conv_row["workspace"],
        "created_at": conv_row["created_at"],
        "updated_at": conv_row["updated_at"],
        "messages": messages
    }


def create_conversation(title: str, workspace: str, conversation_id: str = None) -> str:
    init_db()
    cid = conversation_id or f"chat-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (id, title, workspace, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (cid, title, workspace, now, now)
    )
    conn.commit()
    conn.close()
    return cid


def delete_conversation(conversation_id: str):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


def add_message(conversation_id: str, role: str, text: str, source: str = None, status: str = None, msg_id: str = None) -> str:
    init_db()
    mid = msg_id or f"msg-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if conversation exists
    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
    if not cursor.fetchone():
        # Fallback title generation from prompt
        title = text[:35] + ("..." if len(text) > 35 else "")
        cursor.execute(
            "INSERT INTO conversations (id, title, workspace, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, title, "coding", now, now)
        )
    
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, text, source, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (mid, conversation_id, role, text, source, status, now)
    )
    cursor.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )
    
    conn.commit()
    conn.close()
    return mid


def update_conversation_title(conversation_id: str, new_title: str):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET title = ? WHERE id = ?",
        (new_title, conversation_id)
    )
    conn.commit()
    conn.close()
