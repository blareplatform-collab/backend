"""
BLARE Firebase initialization.
Call init_firebase() once at app startup.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from config.settings import (
    FIREBASE_PROJECT_ID,
    FIREBASE_PRIVATE_KEY,
    FIREBASE_CLIENT_EMAIL
)

db = None


def init_firebase():
    """Initialize Firebase Admin SDK and Firestore client."""
    global db
    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": FIREBASE_PROJECT_ID,
            "private_key": FIREBASE_PRIVATE_KEY,
            "client_email": FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
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
