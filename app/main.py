from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.routers import auth, research, history
import logging

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("market_research_api")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend skeleton for the Market Research Intelligence Assistant",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(research.router, prefix="/api", tags=["research"])
app.include_router(history.router, prefix="/api", tags=["history"])


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    logger.info("Health check requested")
    return {"status": "ok", "service": settings.app_name}
