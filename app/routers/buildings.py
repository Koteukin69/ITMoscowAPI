from typing import List

from fastapi import APIRouter, Depends

from app.auth import verify_token
from app.config import get_settings
from app.models import Building
from app.services.building_service import get_all_buildings

router = APIRouter(prefix="/api", tags=["buildings"])


@router.get("/buildings", response_model=List[Building], dependencies=[Depends(verify_token)])
async def list_buildings() -> List[Building]:
    return await get_all_buildings(get_settings().itmoscow_url)
