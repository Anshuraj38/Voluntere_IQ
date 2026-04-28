from flask import Blueprint, request, jsonify

from models.volunteer import add_volunteer, get_all_volunteers

volunteer_bp = Blueprint("volunteer_bp", __name__)


@volunteer_bp.route("/api/register-volunteer", methods=["POST"])
def register_volunteer():
    payload = request.get_json() or request.form or {}
    name = payload.get("name", "").strip()
    phone = payload.get("phone", "").strip()
    location = payload.get("location", "").strip()
    skills = payload.get("skills") or []
    availability = payload.get("availability", "available").strip()

    if isinstance(skills, str):
        skills = [skill.strip() for skill in skills.split(",") if skill.strip()]

    if not name or not skills:
        return jsonify(success=False, message="Name and at least one skill are required."), 400

    volunteer_id = add_volunteer(name, phone, location, skills, availability or "available")
    return jsonify(success=True, data={"volunteer_id": volunteer_id})


@volunteer_bp.route("/api/get-volunteers", methods=["GET"])
def get_volunteers():
    volunteers = get_all_volunteers()
    return jsonify(success=True, data=volunteers)
