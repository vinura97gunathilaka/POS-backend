from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.api.v1.api import api_router

from app.core.database import engine
from app.models import Base

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SaaS Smart POS API by XerexLabs",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
def on_startup():
    configure_logging()
    logger.info("Smart POS API starting up — environment ready")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified / created")



# Set CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Set global exception handlers
setup_exception_handlers(app)

# Include core routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Backend API",
        "version": "1.0.0",
        "status": "healthy"
    }
