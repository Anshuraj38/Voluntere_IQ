from flask import Blueprint, request, jsonify

from config import Config
from models.database import add_match
from models.need import add_need, get_all_needs, get_need_by_id, update_need_status
from models.volunteer import get_available_volunteers
from services.claude_service import parse_report, match_volunteers as ai_match_volunteers
from services.ocr_service import extract_text_from_upload

needs_bp = Blueprint("needs_bp", __name__)


@needs_bp.route("/api/submit-need", methods=["POST"])
def submit_need():
    form = request.form or {}
    raw_text = form.get("text", "").strip()
    if "file" in request.files and request.files["file"]:
        extracted = extract_text_from_upload(request.files["file"])
        raw_text = extracted.strip() or raw_text

    if not raw_text:
        return jsonify(success=False, message="Please provide text or upload a file."), 400

    parsed = parse_report(raw_text)
    if not parsed:
        return jsonify(success=False, message="Parsing failed. Check your Google API key and network."), 500

    need_id = add_need(
        raw_text=parsed["raw_text"],
        need_type=parsed["need_type"],
        location=parsed["location"],
        urgency_score=parsed["urgency_score"],
        people_affected=parsed["people_affected"],
        skills_required=parsed["skills_required"],
        summary=parsed["summary"],
    )

    matches = []
    volunteers = get_available_volunteers()
    if volunteers:
        matches = ai_match_volunteers(parsed, volunteers)
        for match in matches[:3]:
            add_match(need_id, match["volunteer_id"], match["match_score"], match["reason"])
        if matches:
            update_need_status(need_id, "assigned")

    return jsonify(success=True, data={"need_id": need_id, "matches": matches})


@needs_bp.route("/api/get-needs", methods=["GET"])
def get_needs():
    needs = get_all_needs()
    return jsonify(success=True, data=needs)


@needs_bp.route("/api/resolve-need", methods=["POST"])
def resolve_need():
    payload = request.get_json() or {}
    need_id = payload.get("need_id")
    if not need_id:
        return jsonify(success=False, message="need_id is required."), 400
    need = get_need_by_id(need_id)
    if not need:
        return jsonify(success=False, message="Need not found."), 404
    update_need_status(need_id, "resolved")
    return jsonify(success=True, data={"need_id": need_id, "status": "resolved"})
