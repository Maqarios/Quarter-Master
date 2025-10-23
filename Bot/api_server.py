import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from config import settings
from fastapi import FastAPI

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Quarter Master API", lifespan=lifespan)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": "Quarter Master API", "version": "1.0.0", "docs": "/docs"}


def configure_server() -> uvicorn.Server:
    """Configure and return a Uvicorn server instance."""
    config = uvicorn.Config(
        app, host=settings.api_host, port=settings.api_port, log_level="info"
    )
    server = uvicorn.Server(config)
    return server


async def run_api() -> None:
    try:
        log.info(f"Starting API Server on {settings.api_host}:{settings.api_port}...")
        server = configure_server()
        await server.serve()
    except Exception as e:
        log.error(f"API Server encountered an error: {e}", exc_info=True)
        raise
    finally:
        log.info("API Server has shutdown.")
