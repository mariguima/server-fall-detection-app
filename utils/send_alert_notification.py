from firebase_admin import messaging

from firebase_client import db


def send_alert_notification(user_id, event_data):
    user_doc = db.collection("users").document(user_id).get()
    user = user_doc.to_dict() or {}
    fcm_token = user.get("fcmToken")

    if not fcm_token:
        return

    message = messaging.Message(
        token=fcm_token,
        notification=messaging.Notification(
            title="Fall Detected",
            body="Your camera detected a fall.",
        ),
        data={
            "eventId": event_data["id"],
            "deviceId": event_data["deviceId"],
            "type": "camera_alert",
        },
    )

    try:
        messaging.send(message)
    except Exception as error:
        print("Could not send notification:", error)
