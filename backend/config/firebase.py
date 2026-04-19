"""
BLARE Firebase initialization.
Call init_firebase() once at app startup.
"""
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

db = None


def init_firebase():
    """Initialize Firebase Admin SDK and Firestore client.

    Reads the full service account JSON from the FIREBASE_CREDENTIALS
    environment variable, parses it, and passes it directly to
    credentials.Certificate(). This avoids PEM framing issues that arise
    when individual key fields are reconstructed from separate env vars.
    """
    global db
    try:
        raw = os.environ.get("FIREBASE_CREDENTIALS", "").strip()
        if not raw:
            raise ValueError(
                "FIREBASE_CREDENTIALS environment variable is not set or empty. "
                "Set it to the full Firebase service account JSON string."
            )
        service_account = json.loads(raw)
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] Connected successfully")
        return db
    except Exception as e:
        print(f"[Firebase] Connection failed: {e}")
        raise


def get_db():
    if db is None:
        raise RuntimeError("Firebase not initialized. Call init_firebase() first.")
    return db
