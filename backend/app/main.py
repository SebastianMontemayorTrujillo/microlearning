import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import config
from app.db import Base, SessionLocal, engine
from app.models import AIGeneration  # noqa: F401 - registers all ORM tables
from app.seed import seed_database
from app.services.buffer import buffer_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_database(db)
    task = asyncio.create_task(buffer_worker())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Lilt · Personal learning engine", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list({config.frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"}),
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def local_write_guard(request: Request, call_next):
    # A local single-user service: block browser writes from unrelated websites.
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        origin = request.headers.get("origin")
        allowed = {config.frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"}
        if origin and origin not in allowed:
            return JSONResponse(
                status_code=403, content={"detail": "This origin cannot change your learning data."}
            )
        if "application/json" not in request.headers.get("content-type", ""):
            return JSONResponse(status_code=415, content={"detail": "Send application/json."})
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(router)
