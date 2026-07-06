from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client

from app.core.config import get_settings


@lru_cache
def get_firebase_app() -> firebase_admin.App:
    settings = get_settings()
    cred = credentials.Certificate(settings.google_application_credentials)
    return firebase_admin.initialize_app(cred, {"projectId": settings.firestore_project_id})


@lru_cache
def get_firestore_client() -> Client:
    get_firebase_app()
    return firestore.client()


def get_db() -> Client:
    return get_firestore_client()
