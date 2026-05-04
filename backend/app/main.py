from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import traceback
import asyncio
from .services.watchdog import start_watchdog

from .api.router import api_router
from .core.config import get_settings
from .core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .core.logging_config import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    # Allow all origins in development to prevent CORS blocking
    if settings.app_env == "development":
        origins = ["*"]
    else:
        origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

    app = FastAPI(
        title="System Health Monitoring API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.limiter = limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logging.error("Unhandled exception: %s\n%s", str(exc), traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(exc)},
        )

    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    @app.on_event("startup")
    async def startup_event():
        # Start background tasks
        asyncio.create_task(start_watchdog())

    app.openapi = custom_openapi

    return app


app = create_app()
