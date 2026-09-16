from collections.abc import Generator
from threading import RLock

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import ROOT, config


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    engine = create_engine(
        url, connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_options(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


engine = make_engine(config.database_url or f"sqlite:///{ROOT / 'backend' / 'microlearn.db'}")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
# The local MVP runs one API process. Serialize short writes, never network calls.
write_lock = RLock()


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
