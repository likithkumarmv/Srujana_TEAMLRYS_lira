from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import LiraException, create_error_response
from app.api.v1.health import router as health_router
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.cases import router as cases_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.verification import router as verification_router
from app.api.v1.simulations import router as simulations_router
from app.api.v1.audit import router as audit_router
from app.api.v1.device import router as device_router
from app.api.v1.nfc import router as nfc_router
from app.api.v1.gemini import router as gemini_router
from app.api.v1.payments import router as payments_router, cases_cancel_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting %s in %s environment", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    description="LIRA — Financial Fraud Detection & Investigation Platform Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler
@app.exception_handler(LiraException)
async def lira_exception_handler(request: Request, exc: LiraException):
    return create_error_response(exc)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "request_id": str(request.headers.get("x-request-id", "unknown"))
            }
        }
    )

from fastapi.responses import JSONResponse, FileResponse
import os

# Root route
@app.get("/")
async def root():
    return {
        "product": "LIRA",
        "description": "Financial Fraud Detection & Investigation Platform",
        "docs": "/docs",
        "health": "/health/ready",
        "api_prefix": settings.API_PREFIX,
        "download_apk": "/download-apk"
    }

@app.api_route("/download-apk", methods=["GET", "HEAD"])
async def download_apk():
    apk_path = "C:/Users/sujee/AndroidStudioProjects/Lira/app/src/main/java/com/example/lira/Lira-app-debug.apk"
    if not os.path.exists(apk_path):
        apk_path = "C:/Users/sujee/AndroidStudioProjects/Lira/app/build/outputs/apk/debug/app-debug.apk"
    return FileResponse(
        path=apk_path,
        filename="Lira-Defense.apk",
        media_type="application/vnd.android.package-archive"
    )

# Register Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(cases_router, prefix=settings.API_PREFIX)
app.include_router(transactions_router, prefix=settings.API_PREFIX)
app.include_router(suppliers_router, prefix=settings.API_PREFIX)
app.include_router(verification_router, prefix=settings.API_PREFIX)
app.include_router(simulations_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(device_router, prefix=settings.API_PREFIX)
app.include_router(nfc_router, prefix=settings.API_PREFIX)
app.include_router(gemini_router, prefix=settings.API_PREFIX)
app.include_router(payments_router, prefix=settings.API_PREFIX)
app.include_router(cases_cancel_router, prefix=settings.API_PREFIX)
