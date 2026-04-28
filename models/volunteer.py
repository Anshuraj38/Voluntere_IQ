import json
from models.database import get_connection


def add_volunteer(name, phone, location, skills, availability):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO volunteers (name, phone, location, skills, availability) VALUES (?, ?, ?, ?, ?)",
        (name, phone, location, json.dumps(skills), availability),
    )
    conn.commit()
    volunteer_id = cursor.lastrowid
    conn.close()
    return volunteer_id


def get_all_volunteers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM volunteers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    volunteers = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item["skills"] or "[]")
        volunteers.append(item)
    return volunteers


def get_available_volunteers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM volunteers WHERE availability = 'available' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    volunteers = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item["skills"] or "[]")
        volunteers.append(item)
    return volunteers


def get_volunteer_by_id(volunteer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM volunteers WHERE id = ?", (volunteer_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        item["skills"] = json.loads(item["skills"] or "[]")
        return item
    return None
