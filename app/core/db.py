"""Single import seam for database access.

All services and routers import Session and get_db from here.
The backend is now PostgreSQL via SQLAlchemy.
"""

from sqlalchemy.orm import Session  # noqa: F401 — re-exported for router type hints

from app.core.database import get_db  # noqa: F401

__all__ = ["Session", "get_db"]
