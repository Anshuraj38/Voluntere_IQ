import json
import sqlite3
from sqlite3 import Connection

from config import Config


def get_connection() -> Connection:
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS needs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text TEXT,
            need_type TEXT,
            location TEXT,
            urgency_score INTEGER,
            people_affected INTEGER,
            skills_required TEXT,
            summary TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            location TEXT,
            skills TEXT,
            availability TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            need_id INTEGER,
            volunteer_id INTEGER,
            match_score INTEGER,
            reason TEXT,
            assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (need_id) REFERENCES needs(id),
            FOREIGN KEY (volunteer_id) REFERENCES volunteers(id)
        )
        """
    )
    conn.commit()
    conn.close()


def row_to_dict(row):
    if row is None:
        return None
    result = dict(row)
    if "skills_required" in result and result["skills_required"]:
        try:
            result["skills_required"] = json.loads(result["skills_required"])
        except Exception:
            result["skills_required"] = []
    if "skills" in result and result["skills"]:
        try:
            result["skills"] = json.loads(result["skills"])
        except Exception:
            result["skills"] = []
    return result


def add_match(need_id, volunteer_id, match_score, reason):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO matches (need_id, volunteer_id, match_score, reason) VALUES (?, ?, ?, ?)",
        (need_id, volunteer_id, match_score, reason),
    )
    conn.commit()
    conn.close()


def get_matches_for_need(need_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM matches WHERE need_id = ? ORDER BY match_score DESC LIMIT 3",
        (need_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
