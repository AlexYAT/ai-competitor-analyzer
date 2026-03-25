"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import competitors, health
from app.core.logging import setup_logging


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

app.include_router(health.router)
app.include_router(competitors.router)
