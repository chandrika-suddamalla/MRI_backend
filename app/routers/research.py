from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService

router = APIRouter()
service = ResearchService()


@router.post("/research", response_model=ResearchResponse, status_code=status.HTTP_200_OK)
def create_research(payload: ResearchRequest, current_user: dict[str, str] = Depends(get_current_user)) -> ResearchResponse:
    """Create and persist a research report for the authenticated user."""
    return service.create_research(payload, user_id=current_user["sub"])
