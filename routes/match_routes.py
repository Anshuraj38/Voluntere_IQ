from flask import Blueprint, request, jsonify

from models.database import add_match
from models.need import get_need_by_id, update_need_status
from models.volunteer import get_available_volunteers
from services.claude_service import match_volunteers as ai_match_volunteers

match_bp = Blueprint("match_bp", __name__)


@match_bp.route("/api/match-volunteers", methods=["POST"])
def match_volunteers():
    payload = request.get_json() or {}
    need_id = payload.get("need_id")
    if not need_id:
        return jsonify(success=False, message="need_id is required."), 400

    need = get_need_by_id(need_id)
    if not need:
        return jsonify(success=False, message="Need not found."), 404

    volunteers = get_available_volunteers()
    if not volunteers:
        return jsonify(success=False, message="No available volunteers."), 200

    matches = ai_match_volunteers(need, volunteers)
    for match in matches[:3]:
        add_match(need_id, match["volunteer_id"], match["match_score"], match["reason"])
    if matches:
        update_need_status(need_id, "assigned")

    return jsonify(success=True, data={"matches": matches})


@match_bp.route("/api/stats", methods=["GET"])
def stats():
    from models.need import get_all_needs
    from models.volunteer import get_all_volunteers

    needs = get_all_needs()
    volunteers = get_all_volunteers()
    resolved = sum(1 for need in needs if need.get("status") == "resolved")
    pending = sum(1 for need in needs if need.get("status") == "pending")
    active_volunteers = sum(1 for volunteer in volunteers if volunteer.get("availability") == "available")

    return jsonify(
        success=True,
        data={
            "total_needs": len(needs),
            "resolved": resolved,
            "pending": pending,
            "active_volunteers": active_volunteers,
            "available_volunteers": len(volunteers),
        },
    )
