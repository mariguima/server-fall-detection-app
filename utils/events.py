from datetime import datetime, timezone

from firebase_admin import firestore

from firebase_client import db


def parse_esp_timestamp(timestamp):
    if timestamp is None:
        return None

    timestamp = int(timestamp)
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000

    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def create_fall_event(
    device_id,
    user_id,
    esp_timestamp=None,
    source="event",
    frame_sequence=None,
    fall_score=None,
):
    event = {
        "deviceId": device_id,
        "userId": user_id,
        "espTimestamp": esp_timestamp,
        "serverTimestamp": firestore.SERVER_TIMESTAMP,
        "status": "warning",
        "source": source,
    }

    if frame_sequence is not None:
        event["frameSequence"] = frame_sequence

    if fall_score is not None:
        event["fallScore"] = fall_score

    _, ref = db.collection("events").add(event)
    return ref.id
