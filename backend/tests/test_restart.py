"""Real process restart against an isolated on-disk database, without paid API calls."""

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx


def test_progress_and_bookmarks_survive_backend_restart(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'restart.db'}", "OPENAI_API_KEY": ""}

    @contextmanager
    def server():
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            with httpx.Client(base_url=url, timeout=3) as client:
                for _ in range(100):
                    if process.poll() is not None:
                        raise AssertionError("Isolated backend did not start")
                    try:
                        if client.get("/api/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.05)
                else:
                    raise AssertionError("Backend health check timed out")
                yield client
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    with server() as client:
        assert (
            client.post(
                "/api/onboarding", json={"subjects": ["Computer Science"], "level": "beginner"}
            ).status_code
            == 200
        )
        card = client.get("/api/feed?limit=1").json()["cards"][0]
        for kind in ("shown", "known"):
            assert (
                client.post(
                    "/api/interactions", json={"presentation_id": card["presentation_id"], "kind": kind}
                ).status_code
                == 200
            )
        assert client.put(f"/api/cards/{card['id']}/saved", json={"saved": True}).status_code == 200
    with server() as restarted:
        assert restarted.get("/api/settings").json()["onboarded"]
        assert restarted.get("/api/progress").json()["encountered"] == 1
        saved = restarted.get("/api/saved").json()["cards"]
        assert len(saved) == 1 and saved[0]["id"] == card["id"]
        assert saved[0]["mastery"]["mastery"] == 0.08
        assert saved[0]["mastery"]["next_review"] is not None
