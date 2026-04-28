import json
from models.database import get_connection


def add_need(raw_text, need_type, location, urgency_score, people_affected, skills_required, summary):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO needs (raw_text, need_type, location, urgency_score, people_affected, skills_required, summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            raw_text,
            need_type,
            location,
            urgency_score,
            people_affected,
            json.dumps(skills_required),
            summary,
        ),
    )
    conn.commit()
    need_id = cursor.lastrowid
    conn.close()
    return need_id


def get_all_needs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM needs ORDER BY urgency_score DESC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    needs = []
    for row in rows:
        item = dict(row)
        item["skills_required"] = json.loads(item["skills_required"] or "[]")
        needs.append(item)
    return needs


def get_need_by_id(need_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM needs WHERE id = ?", (need_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        item["skills_required"] = json.loads(item["skills_required"] or "[]")
        return item
    return None


def update_need_status(need_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE needs SET status = ? WHERE id = ?", (status, need_id))
    conn.commit()
    conn.close()
