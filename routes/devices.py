from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from firebase_admin import auth

from firebase_client import db
from middleware.auth import user_auth
from utils.generate_api_key import generate_api_key
from utils.serialization import public_doc

devices_bp = Blueprint("devices", __name__)


@devices_bp.get("/")
@user_auth
def list_devices():
    try:
        snapshot = (
            db.collection("devices")
            .where("userId", "==", g.user["uid"])
            .stream()
        )
        devices = [public_doc(doc, hidden_fields=["apiKey"]) for doc in snapshot]
        return jsonify({"devices": devices}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@devices_bp.post("/")
def register_device():
    payload = request.get_json(silent=True) or {}
    device_id = payload.get("deviceId")
    user_email = payload.get("userEmail")

    if not device_id or not user_email:
        return jsonify({"error": "Invalid request"}), 400

    try:
        user = auth.get_user_by_email(user_email)
        auth.get_user(user.uid)

        ref = db.collection("devices").document(device_id)
        existing = ref.get()

        if existing.exists:
            device = existing.to_dict() or {}
            return jsonify({
                "error": "Device already registered",
                "apiKey": device.get("apiKey"),
            }), 409

        api_key = generate_api_key()
        ref.set({
            "userId": user.uid,
            "apiKey": api_key,
            "registeredAt": datetime.now(timezone.utc),
        })

        return jsonify({"registered": True, "apiKey": api_key}), 201
    except auth.UserNotFoundError:
        return jsonify({"error": "User not found"}), 404
    except Exception as error:
        return jsonify({"error": str(error)}), 500
