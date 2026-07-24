import logging
import re

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.routers import auth, research, history

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

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")

    if origin and (
        origin in settings.allowed_origins
        or re.match(r"https://.*\.vercel\.app$", origin) is not None
    ):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"

    if request.method == "OPTIONS":
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Max-Age"] = "600"

    return response

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(research.router, prefix="/api", tags=["research"])
app.include_router(history.router, prefix="/api", tags=["history"])


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    logger.info("Health check requested")
    return {"status": "ok", "service": settings.app_name}
