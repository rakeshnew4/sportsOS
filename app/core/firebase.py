import logging
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, credentials, firestore, messaging
from google.cloud.firestore import Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_firebase_app() -> firebase_admin.App | None:
    """Lazily initializes the Firebase Admin app. Returns None if credentials
    aren't configured (e.g. a dev machine without firebase_serviceaccount.json)
    so callers can degrade gracefully instead of crashing the request."""
    settings = get_settings()
    if not os.path.exists(settings.google_application_credentials):
        logger.warning(
            "Firebase credentials not found at %s — realtime mirroring and push "
            "notifications are disabled.",
            settings.google_application_credentials,
        )
        return None
    cred = credentials.Certificate(settings.google_application_credentials)
    return firebase_admin.initialize_app(cred, {"projectId": settings.firestore_project_id})


def get_firestore_client() -> Client | None:
    app = get_firebase_app()
    if app is None:
        return None
    return firestore.client(app)


def get_messaging():
    """Returns the firebase_admin.messaging module if Firebase is configured, else None."""
    return messaging if get_firebase_app() is not None else None


def get_auth():
    """Returns the firebase_admin.auth module if Firebase is configured, else None."""
    return auth if get_firebase_app() is not None else None
