import logging
import time
import uuid

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .api.router import api_router
from .core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logger = logging.getLogger("backend.http")

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if settings.strict_cors_in_non_dev and settings.app_env.lower() != "development":
        unsafe_origins = [origin for origin in origins if "localhost" in origin or "127.0.0.1" in origin]
        if unsafe_origins:
            raise ValueError("CORS_ORIGINS contains local origins while STRICT_CORS_IN_NON_DEV is enabled")

    app = FastAPI(
        title="System Health Monitoring API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.get("/")
    def root() -> dict:
        return {
            "service": "System Health Monitoring API",
            "docs": "/docs",
            "api_prefix": settings.api_prefix,
            "health": f"{settings.api_prefix}/health/live",
        }

    # ✅ Include your routes
    app.include_router(api_router, prefix=settings.api_prefix)

    # ✅ Add Swagger Authorize (JWT Bearer)
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description="API with JWT Authentication",
            routes=app.routes,
        )

        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }

        openapi_schema["security"] = [{"BearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app


app = create_app()