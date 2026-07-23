from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.services.history_service import HistoryService

router = APIRouter()
service = HistoryService()


@router.get("/history", response_model=list[dict], status_code=status.HTTP_200_OK)
def get_history(current_user: dict[str, str] = Depends(get_current_user)) -> list[dict]:
    """Return mock historical reports for an authenticated user."""
    _ = current_user
    return service.get_history()
