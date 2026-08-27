import json
import os

import firebase_admin
from firebase_admin import auth, credentials, firestore, messaging, storage


def _initialize_firebase():
    if firebase_admin._apps:
        return

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if service_account_path:
        with open(service_account_path, encoding="utf-8") as service_account_file:
            credentials_dict = json.load(service_account_file)
    elif service_account:
        credentials_dict = json.loads(service_account)
    else:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT or FIREBASE_SERVICE_ACCOUNT_PATH is required"
        )

    options = {}
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
    if storage_bucket:
        options["storageBucket"] = storage_bucket

    firebase_admin.initialize_app(credentials.Certificate(credentials_dict), options)


_initialize_firebase()

db = firestore.client()
