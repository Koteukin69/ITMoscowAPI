from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_token
from app.config import get_settings
from app.models import Schedule, ScheduleDayRequest
from app.services.schedule_service import get_schedule_for_day

router = APIRouter(prefix="/itmoscow/api/v1/schedule", tags=["schedule"])


@router.post("/day", response_model=Schedule, dependencies=[Depends(verify_token)])
async def schedule_for_day(body: ScheduleDayRequest) -> Schedule:
    try:
        return await get_schedule_for_day(
            base_url=get_settings().itmoscow_url,
            building_key=body.building,
            group_name=body.group,
            weekday=body.weekday,
            apply_replacements=body.replacements,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
