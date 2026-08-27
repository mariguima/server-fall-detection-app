from io import BytesIO
from threading import Lock

from flask import Blueprint, g, jsonify, request
from PIL import Image

from middleware.auth import device_auth
from utils.events import create_fall_event, parse_esp_timestamp

try:
    from model.model import predict, predict_image
except ImportError:
    predict = None
    predict_image = None

frames_bp = Blueprint("frames", __name__)
REQUIRED_CONSECUTIVE_FALL_FRAMES = 3

_frame_states = {}
_frame_states_lock = Lock()


def _update_frame_state(
    device_id,
    result,
    frame_sequence,
    frame_timestamp,
    frame_image_bytes=None,
):
    event_id = None

    with _frame_states_lock:
        state = _frame_states.setdefault(
            device_id,
            {
                "consecutiveFallFrames": 0,
                "alertActive": False,
                "lastFrameSequence": None,
                "lastFrameTimestamp": None,
            },
        )

        state["lastFrameSequence"] = frame_sequence
        state["lastFrameTimestamp"] = frame_timestamp

        if result["isFall"]:
            state["consecutiveFallFrames"] += 1
        else:
            state["consecutiveFallFrames"] = 0
            state["alertActive"] = False

        should_create_event = (
            state["consecutiveFallFrames"] >= REQUIRED_CONSECUTIVE_FALL_FRAMES
            and not state["alertActive"]
        )

        if should_create_event:
            event_id = create_fall_event(
                device_id=device_id,
                user_id=g.device["userId"],
                esp_timestamp=frame_timestamp,
                source="frames",
                frame_sequence=frame_sequence,
                fall_score=result["fallScore"],
                frame_image_bytes=frame_image_bytes,
                frame_content_type="image/jpeg",
            )
            state["alertActive"] = True

        return {
            "consecutiveFallFrames": state["consecutiveFallFrames"],
            "requiredConsecutiveFallFrames": REQUIRED_CONSECUTIVE_FALL_FRAMES,
            "alertActive": state["alertActive"],
            "eventCreated": event_id is not None,
            "eventId": event_id,
        }


@frames_bp.post("/")
@device_auth
def analyze_frame():
    if predict is None or predict_image is None:
        return jsonify({"error": "Model predict function is not implemented"}), 501

    try:
        if request.mimetype == "image/jpeg":
            frame_image_bytes = request.get_data()
            image = Image.open(BytesIO(frame_image_bytes))
        elif "frame" in request.files:
            frame_image_bytes = request.files["frame"].read()
            image = Image.open(BytesIO(frame_image_bytes))
        else:
            payload = request.get_json(silent=True) or {}
            result = predict(payload)
            return jsonify({"result": result}), 200

        frame_sequence = request.headers.get("x-frame-sequence")
        raw_frame_timestamp = request.headers.get("x-frame-timestamp")
        frame_timestamp = parse_esp_timestamp(raw_frame_timestamp)
        result = predict_image(image)
        print(
            "Frame received:",
            {
                "deviceId": g.device_id,
                "sequence": frame_sequence,
                "timestamp": raw_frame_timestamp,
                "bytes": request.content_length,
                "isFall": result["isFall"],
                "fallScore": result["fallScore"],
            },
            flush=True,
        )
        frame_state = _update_frame_state(
            g.device_id,
            result,
            frame_sequence,
            frame_timestamp,
            frame_image_bytes,
        )

        return jsonify({"result": result, "frameState": frame_state}), 200
    except (TypeError, ValueError, OSError):
        return jsonify({"error": "Invalid frame timestamp"}), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 500
