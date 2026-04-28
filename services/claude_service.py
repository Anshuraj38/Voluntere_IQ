import base64
import json
import re
import requests
from config import Config

NL_URL = "https://language.googleapis.com/v1/documents"
VISION_URL = "https://vision.googleapis.com/v1/images:annotate"

KNOWN_SKILLS = [
    "Medical",
    "Construction",
    "Teaching",
    "Counseling",
    "Logistics",
    "Tech",
    "Food",
    "Shelter",
    "Water",
    "Rescue",
    "Communications",
    "Education",
    "Support",
]

NEED_TYPE_KEYWORDS = [
    ("Medical", ["medical", "health", "injury", "doctor", "clinic", "patient"]),
    ("Construction", ["construction", "repair", "debris", "bridge", "road", "build"]),
    ("Teaching", ["teach", "education", "training", "school", "students"]),
    ("Counseling", ["counsel", "mental", "support", "psychological", "therapy"]),
    ("Logistics", ["logistics", "supply", "transport", "coordinate", "delivery"]),
    ("Tech", ["tech", "technology", "software", "hardware", "computer"]),
    ("Food", ["food", "water", "nutrition", "meal", "hunger"]),
]

URGENCY_KEYWORDS = [
    ("critical", 10),
    ("emergency", 9),
    ("urgent", 9),
    ("immediately", 8),
    ("as soon as possible", 8),
    ("high priority", 8),
    ("soon", 7),
    ("important", 6),
]


def _analyze_entities(text):
    if not Config.GOOGLE_API_KEY:
        return {}

    payload = {
        "document": {"type": "PLAIN_TEXT", "content": text},
        "encodingType": "UTF8",
    }
    try:
        response = requests.post(f"{NL_URL}:analyzeEntities?key={Config.GOOGLE_API_KEY}", json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def _call_google_vision(image_bytes):
    if not Config.GOOGLE_API_KEY:
        return None
    payload = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_bytes).decode("utf-8")},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}],
            }
        ]
    }
    try:
        response = requests.post(f"{VISION_URL}?key={Config.GOOGLE_API_KEY}", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        annotations = result.get("responses", [{}])[0]
        full_text = annotations.get("fullTextAnnotation")
        if full_text and full_text.get("text"):
            return full_text["text"].strip()
        text_annotations = annotations.get("textAnnotations")
        if text_annotations and len(text_annotations) > 0:
            return text_annotations[0].get("description", "").strip()
    except Exception:
        return None
    return None


def _extract_location(entities):
    for entity in entities.get("entities", []):
        if entity.get("type") == "LOCATION":
            return entity.get("name")
        if entity.get("type") == "ORGANIZATION" and any(place in entity.get("name", "").lower() for place in ["village", "city", "district", "sector", "town"]):
            return entity.get("name")
    return None


def _parse_location_from_text(text):
    lower = text.lower()
    patterns = [
        r"location\s*[:\-]\s*(.+?)(?:[\n\r]|$)",
        r"address\s*[:\-]\s*(.+?)(?:[\n\r]|$)",
        r"at\s+([A-Z][a-zA-Z0-9 ,]+?)(?:\.|,|$)",
        r"in\s+([A-Z][a-zA-Z0-9 ,]+?)(?:\.|,|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            location = match.group(1).strip()
            if len(location) > 1 and not location.lower().startswith("reported"):
                return location
    # last fallback: find common location words
    for keyword in ["sector", "village", "town", "city", "district", "region", "zone"]:
        idx = lower.find(keyword)
        if idx != -1:
            snippet = text[idx:idx + 60].split("\n")[0].strip()
            if len(snippet) > 0:
                return snippet
    return None


def _extract_skills(text):
    skills = set()
    lower = text.lower()
    for skill in KNOWN_SKILLS:
        if skill.lower() in lower:
            skills.add(skill)
    return sorted(skills)


def _infer_need_type(text):
    lower = text.lower()
    for label, keywords in NEED_TYPE_KEYWORDS:
        for keyword in keywords:
            if keyword in lower:
                return label
    return "General"


def _parse_urgency(text):
    lower = text.lower()
    for keyword, score in URGENCY_KEYWORDS:
        if keyword in lower:
            return score
    if "critical" in lower or "immediate" in lower:
        return 9
    return 5


def _parse_people_affected(text):
    match = re.search(r"(\d+)\s*(people|persons|families|family|households|students|patients|families)", text, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*(?:affected|impacted)", text, re.I)
    if match:
        return int(match.group(1))
    return 1


def _parse_summary(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return sentences[0].strip() if sentences else text.strip()


def parse_report(raw_text):
    if not raw_text:
        return None

    entities = _analyze_entities(raw_text) if Config.GOOGLE_API_KEY else {}
    location = _extract_location(entities) or _parse_location_from_text(raw_text) or "Unknown"
    skills_required = _extract_skills(raw_text)
    need_type = _infer_need_type(raw_text)
    urgency_score = _parse_urgency(raw_text)
    people_affected = _parse_people_affected(raw_text)
    summary = _parse_summary(raw_text)

    return {
        "raw_text": raw_text,
        "need_type": need_type,
        "location": location,
        "urgency_score": urgency_score,
        "people_affected": people_affected,
        "skills_required": skills_required,
        "summary": summary,
    }


def match_volunteers(need, volunteers):
    if not volunteers:
        return []

    def score_volunteer(volunteer):
        skill_overlap = len(set(volunteer.get("skills", [])).intersection(set(need.get("skills_required", []))))
        location_score = 5 if volunteer.get("location", "").lower() == need.get("location", "").lower() else 0
        urgency_bonus = min(10, need.get("urgency_score", 5))
        return skill_overlap * 15 + location_score + urgency_bonus

    matches = []
    for volunteer in volunteers:
        score = score_volunteer(volunteer)
        reason_parts = []
        if set(volunteer.get("skills", [])).intersection(set(need.get("skills_required", []))):
            reason_parts.append("Skills match")
        if volunteer.get("location", "").lower() == need.get("location", "").lower():
            reason_parts.append("Same location")
        if not reason_parts:
            reason_parts.append("General availability")

        matches.append(
            {
                "volunteer_id": volunteer.get("id"),
                "name": volunteer.get("name", "Unknown"),
                "match_score": min(100, score),
                "reason": ", ".join(reason_parts),
            }
        )

    matches.sort(key=lambda item: item["match_score"], reverse=True)
    return matches[:3]
