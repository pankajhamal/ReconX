"""ReconX API. Run with:  uvicorn app.main:app --reload"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import FRONTEND_URL
from app.core.database import create_tables
from app.routes import uploads


@asynccontextmanager
async def lifespan(app):
    create_tables()  # create any missing tables when the server starts
    yield


app = FastAPI(title="ReconX", lifespan=lifespan)

# Allow the React dashboard to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
