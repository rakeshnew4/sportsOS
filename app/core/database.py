"""SQLAlchemy engine, session factory, and declarative Base."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


# Module-level engine / session factory created lazily on first import after
# settings are resolved (so tests can override DATABASE_URL via env before import).
engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_all_tables():
    """Create all tables. Called once at app startup."""
    # Import ORM models so their metadata is registered with Base before create_all.
    import app.db.orm  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _run_additive_migrations()


def _run_additive_migrations():
    """create_all only adds missing tables, never columns to existing ones.
    There's no migration framework here, so hand-roll the few additive,
    idempotent ALTERs needed to evolve tables already deployed."""
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN NOT NULL DEFAULT false"))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email) WHERE email IS NOT NULL"
        ))


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
