from datetime import date, datetime


def serialize_firestore_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: serialize_firestore_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [serialize_firestore_value(item) for item in value]

    return value


def public_doc(doc, hidden_fields=None):
    data = doc.to_dict() or {}

    for field in hidden_fields or []:
        data.pop(field, None)

    return serialize_firestore_value({"id": doc.id, **data})
