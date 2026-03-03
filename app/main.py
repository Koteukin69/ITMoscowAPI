from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.routers import buildings, groups, schedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()
    yield


app = FastAPI(
    title="ITMoscow API",
    description="Unofficial API for IT Moscow College (it-moscow.pro)",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(buildings.router)
app.include_router(groups.router)
app.include_router(schedule.router)
