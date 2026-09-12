from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.api.v1.api import api_router

from app.core.database import engine, SessionLocal, run_auto_migrations
from app.models import Base
from app.core.audit_listener import register_audit_listeners
from app.core.audit_context import set_audit_context, reset_audit_context
from app.core.security import ALGORITHM
from jose import jwt
from fastapi import Request

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SaaS Smart POS API by XerexLabs",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.middleware("http")
async def audit_context_middleware(request: Request, call_next):
    """Intercepts request to track IP, User-Agent, endpoint, and token context for audits."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        ip = request.headers.get("X-Real-IP").strip()
    else:
        ip = request.client.host if request.client else None

    user_agent = request.headers.get("user-agent")
    endpoint = request.url.path
    method = request.method

    init_context = {
        "ip_address": ip,
        "user_agent": user_agent,
        "endpoint": endpoint,
        "http_method": method
    }

    # Extract user_id from Bearer token if present
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                init_context["user_id"] = int(user_id)
        except Exception:
            pass

    reset_audit_context(init_context)
    try:
        response = await call_next(request)
        set_audit_context(status_code=response.status_code)
        return response
    finally:
        reset_audit_context({})

@app.on_event("startup")
def on_startup():
    configure_logging()
    logger.info("Smart POS API starting up — environment ready")
    Base.metadata.create_all(bind=engine)
    try:
        run_auto_migrations(engine)
        logger.info("Auto migrations executed successfully")
    except Exception as e:
        logger.warning(f"Auto migration note: {e}")
    logger.info("Database tables verified / created (Audit trail engine active)")

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
