"""Single import seam for Firestore access.

Services and routers import Client/FieldFilter/transactional/get_db from here
instead of from google.cloud.firestore directly, so the backend can be swapped
between real Firestore and the local JSON fake (app/core/fake_firestore.py)
with one config value (DATA_BACKEND) and no changes anywhere else.
"""

from app.core.config import get_settings

if get_settings().data_backend == "local_json":
    from app.core.fake_firestore import FakeClient as Client
    from app.core.fake_firestore import FieldFilter, get_db, transactional
else:
    from google.cloud.firestore import Client, FieldFilter, transactional

    from app.core.firebase import get_db

__all__ = ["Client", "FieldFilter", "transactional", "get_db"]
