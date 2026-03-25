"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import competitors, health
from app.core.logging import setup_logging

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(_PROJECT_ROOT / "templates"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="AI Competitor Analyzer",
    description="MVP: discover competitors via search, filter with LLM, prepare for parsing and analysis.",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(_PROJECT_ROOT / "static")), name="static")
app.include_router(health.router)
app.include_router(competitors.router)


@app.get("/")
def ui_index(request: Request):
    """Lightweight demo UI (HTML + CSS + JS)."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/ui", include_in_schema=False)
def ui_alias(request: Request):
    """Alternate path for the same demo page."""
    return templates.TemplateResponse(request, "index.html")
