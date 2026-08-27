import os
from datetime import datetime, timezone
from urllib.parse import quote
from uuid import uuid4

from firebase_admin import firestore, storage

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
    frame_image_bytes=None,
    frame_content_type="image/jpeg",
):
    ref = db.collection("events").document()

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

    if frame_image_bytes:
        image = upload_event_frame(
            event_id=ref.id,
            device_id=device_id,
            frame_image_bytes=frame_image_bytes,
            content_type=frame_content_type,
        )
        event.update(image)

    ref.set(event)
    return ref.id


def upload_event_frame(event_id, device_id, frame_image_bytes, content_type):
    if not os.getenv("FIREBASE_STORAGE_BUCKET"):
        raise RuntimeError("FIREBASE_STORAGE_BUCKET environment variable is required")

    bucket = storage.bucket()
    storage_path = f"events/{event_id}/frames/{device_id}.jpg"
    download_token = str(uuid4())
    blob = bucket.blob(storage_path)
    blob.metadata = {"firebaseStorageDownloadTokens": download_token}
    blob.upload_from_string(frame_image_bytes, content_type=content_type)

    encoded_path = quote(storage_path, safe="")
    image_url = (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
        f"{encoded_path}?alt=media&token={download_token}"
    )

    return {
        "frameImageUrl": image_url,
        "frameStorageBucket": bucket.name,
        "frameStoragePath": storage_path,
    }
