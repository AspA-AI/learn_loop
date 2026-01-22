import logging
import logging.config
import colorlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from core.config import settings
from routes import session, parent, auth
from pathlib import Path
from starlette.staticfiles import StaticFiles

# Configure colored logging using dictConfig (works with uvicorn)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        }
    },
    "handlers": {
        "default": {
            "formatter": "colored",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"]
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["default"],
            "propagate": False
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["default"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "WARNING",
            "handlers": ["default"],
            "propagate": False
        },
        "httpx": {
            "level": "WARNING",
            "handlers": ["default"],
            "propagate": False
        },
    }
}

# Apply logging configuration
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG
)

# Validation Error Handler - handles Pydantic validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors and return user-friendly messages"""
    errors = exc.errors()
    error_messages = []
    MIN_PASSWORD_LENGTH = 6  # Match the constant in auth.py
    
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_type = error.get("type", "")
        ctx = error.get("ctx", {})
        
        # Format user-friendly messages based on field and error type
        if "password" in field.lower():
            if "string_too_short" in error_type:
                min_length = ctx.get("min_length", MIN_PASSWORD_LENGTH)
                message = f"Password must be at least {min_length} characters long"
            elif "value_error" in error_type:
                # Extract the actual ValueError message from context
                if "error" in ctx and isinstance(ctx["error"], ValueError):
                    # Get the message from the ValueError object
                    message = str(ctx["error"])
                else:
                    # Fallback: remove "Value error, " prefix if present
                    message_str = str(message)
                    if message_str.startswith("Value error, "):
                        message = message_str.replace("Value error, ", "", 1)
                    else:
                        message = message_str
                # Handle password length errors
                if "too long" in message.lower() or "no more than" in message.lower():
                    message = "Password must be between 6 and 8 characters long."
        elif "email" in field.lower():
            if "value_error" in error_type or "email" in error_type:
                message = "Please enter a valid email address"
        
        error_messages.append(str(message))
    
    # Return the first error message (most relevant)
    detail = error_messages[0] if error_messages else "Validation error"
    
    return JSONResponse(
        status_code=422,
        content={"detail": detail},
    )

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred.", "detail": str(exc) if settings.DEBUG else None},
    )

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(session.router, prefix="/api/v1")
app.include_router(parent.router, prefix="/api/v1")

# -----------------------------------------------------------------------------
# Optional: serve built frontend (single-service deploy)
# Docker build copies Vite output to api/static
# -----------------------------------------------------------------------------
_static_dir = Path(__file__).resolve().parent / "static"
if getattr(settings, "SERVE_CLIENT", False) and _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        # Never intercept API routes
        if path.startswith("api/") or path.startswith("api"):
            return JSONResponse(status_code=404, content={"message": "Not Found"})

        index_file = _static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(status_code=404, content={"message": "Frontend not built"})

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Learn Loop API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Learn Loop API...")
    from services.weaviate_service import weaviate_service
    weaviate_service.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the Learn Loop API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_config=LOGGING_CONFIG)

