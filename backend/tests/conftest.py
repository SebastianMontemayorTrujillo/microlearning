import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.db import Base, get_db, make_engine
from app.main import app
from app.seed import seed_database


@pytest.fixture
def factory(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "openai_api_key", "")
    engine = make_engine(f"sqlite:///{tmp_path / 'learning.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        seed_database(db)
    yield sessions
    engine.dispose()


@pytest.fixture
def db(factory):
    with factory() as session:
        yield session


@pytest.fixture
def client(factory):
    def database():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = database
    # No lifespan: seed, worker and persistent storage are isolated from real user data.
    client = TestClient(app, raise_server_exceptions=True)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()
