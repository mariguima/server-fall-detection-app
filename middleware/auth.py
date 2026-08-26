from functools import wraps

from flask import g, jsonify, request
from firebase_admin import auth

from firebase_client import db


def user_auth(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        prefix = "Bearer "

        if not authorization.startswith(prefix):
            return jsonify({"error": "Missing token"}), 401

        token = authorization[len(prefix):]

        try:
            g.user = auth.verify_id_token(token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return route(*args, **kwargs)

    return wrapper


def device_auth(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        payload = request.get_json(silent=True) or {}
        api_key = request.headers.get("x-api-key")
        device_id = request.headers.get("x-device-id") or payload.get("deviceId")

        if not api_key or not device_id:
            return jsonify({"error": "Missing credentials"}), 401

        try:
            doc = db.collection("devices").document(device_id).get()
            device = doc.to_dict() if doc.exists else None

            if not device or device.get("apiKey") != api_key:
                return jsonify({"error": "Invalid device credentials"}), 401

            g.device = device
            g.device_id = device_id
        except Exception as error:
            return jsonify({"error": str(error)}), 500

        return route(*args, **kwargs)

    return wrapper
