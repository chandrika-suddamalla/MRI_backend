from fastapi import APIRouter, status
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()
service = AuthService()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""
    return service.login(payload)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> TokenResponse:
    """Register a new user account and return a JWT access token."""
    return service.register(payload)
