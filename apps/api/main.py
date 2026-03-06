"""FastAPI application — AI Update Tracker MVP.

Serves the REST API and static frontend files.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apps.api.database import init_db
from apps.api.routers import events, meta

# ---------------------------------------------------------------------------
# Lifespan — initialise DB on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup / shutdown logic."""
    init_db()
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Update Tracker API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(events.router)
app.include_router(meta.router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health_check():
    """Health-check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static files — serve apps/web/ at "/"
# ---------------------------------------------------------------------------

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

if (WEB_DIR / "css").is_dir():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")

if (WEB_DIR / "js" / "cards").is_dir():
    app.mount("/js/cards", StaticFiles(directory=str(WEB_DIR / "js" / "cards")), name="js-cards")

if (WEB_DIR / "js").is_dir():
    app.mount("/js", StaticFiles(directory=str(WEB_DIR / "js")), name="js")


@app.get("/")
def serve_index():
    """Serve the frontend index.html."""
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index))
