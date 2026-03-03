from typing import List, Optional

from fastapi import APIRouter, Depends

from app.auth import verify_token
from app.config import get_settings
from app.models import GroupItem, GroupsFilterRequest
from app.services.building_service import get_all_buildings
from app.services.group_service import get_all_groups, get_groups_for_building

router = APIRouter(prefix="/api", tags=["groups"])


@router.get("/groups", response_model=List[GroupItem], dependencies=[Depends(verify_token)])
async def list_all_groups() -> List[GroupItem]:
    settings = get_settings()
    buildings = await get_all_buildings(settings.itmoscow_url)
    return await get_all_groups(buildings, settings.itmoscow_url)


@router.post("/groups", response_model=List[GroupItem], dependencies=[Depends(verify_token)])
async def filter_groups(body: GroupsFilterRequest) -> List[GroupItem]:
    settings = get_settings()
    buildings = await get_all_buildings(settings.itmoscow_url)

    # Filter buildings if building key is provided
    if body.building:
        buildings = [b for b in buildings if b.key == body.building]

    groups = await get_all_groups(buildings, settings.itmoscow_url)

    # Filter by group key if provided
    if body.key:
        groups = [g for g in groups if g.key == body.key]

    return groups
