from fastapi import FastAPI

from app.routers import buildings, groups, schedule

app = FastAPI(
    title="ITMoscow API",
    description="Unofficial API for IT Moscow College (it-moscow.pro)",
    version="2.0.0",
)

app.include_router(buildings.router)
app.include_router(groups.router)
app.include_router(schedule.router)
