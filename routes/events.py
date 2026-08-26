from flask import Blueprint, g, jsonify, request

from firebase_client import db
from middleware.auth import device_auth, user_auth
from utils.events import create_fall_event, parse_esp_timestamp
from utils.serialization import public_doc, serialize_firestore_value

events_bp = Blueprint("events", __name__)


@events_bp.get("/<event_id>")
@user_auth
def get_event(event_id):
    try:
        doc = db.collection("events").document(event_id).get()
        if not doc.exists:
            return jsonify({"error": "Event not found"}), 404

        event = doc.to_dict() or {}
        if event.get("userId") != g.user["uid"]:
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify(public_doc(doc, hidden_fields=["userId"])), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@events_bp.get("/")
@user_auth
def list_events():
    try:
        snapshot = (
            db.collection("events")
            .where("userId", "==", g.user["uid"])
            .stream()
        )
        events = [public_doc(doc, hidden_fields=["userId"]) for doc in snapshot]
        return jsonify({"events": events}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@events_bp.post("/")
@device_auth
def create_event():
    payload = request.get_json(silent=True) or {}
    timestamp = payload.get("timestamp")
    device_id = g.device_id
    user_id = g.device["userId"]

    try:
        esp_timestamp = parse_esp_timestamp(timestamp)
    except (TypeError, ValueError, OSError):
        return jsonify({"error": "Invalid timestamp"}), 400

    try:
        event_id = create_fall_event(device_id, user_id, esp_timestamp)
        return jsonify({"received": True, "eventId": event_id}), 201
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@events_bp.patch("/<event_id>/confirm")
@user_auth
def confirm_event(event_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")

    if status not in ["fall", "no_fall"]:
        return jsonify({"error": "Invalid status value"}), 400

    try:
        ref = db.collection("events").document(event_id)
        doc = ref.get()

        if not doc.exists:
            return jsonify({"error": "Event not found"}), 404

        event = doc.to_dict() or {}
        if event.get("userId") != g.user["uid"]:
            return jsonify({"error": "Unauthorized"}), 403

        if event.get("status") != "warning":
            return jsonify({"error": "Event already confirmed"}), 409

        ref.update({"status": status})
        return jsonify(serialize_firestore_value({"eventId": event_id, "status": status})), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
