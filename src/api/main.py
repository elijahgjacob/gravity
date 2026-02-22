"""FastAPI application initialization."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import health, retrieval
from src.core.dependencies import init_dependencies, shutdown_dependencies
from src.core.logging_config import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Ad Retrieval API...")
    await init_dependencies()
    logger.info("Ad Retrieval API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ad Retrieval API...")
    await shutdown_dependencies()
    logger.info("Ad Retrieval API shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Ad Retrieval API",
    description="""
    High-performance ad retrieval system that processes user queries with context,
    determines commercial intent, and retrieves relevant advertising campaigns.
    
    **Target Latency:** < 100ms (p95)
    
    **Features:**
    - Ad eligibility scoring (0.0-1.0)
    - Category extraction (1-10 categories)
    - Campaign retrieval and ranking (top 1,000)
    - Context-based targeting
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_latency_header(request: Request, call_next):
    """
    Middleware to track and add latency information to responses.
    
    Args:
        request: Incoming request
        call_next: Next middleware/handler
    
    Returns:
        Response with X-Latency-Ms header
    """
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Latency-Ms"] = f"{latency_ms:.2f}"
    
    # Log slow requests (>100ms)
    if latency_ms > 100:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {latency_ms:.2f}ms"
        )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: Request that caused the error
        exc: Exception that was raised
    
    Returns:
        JSON error response
    """
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path}",
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path)
        }
    )


# Register routes
app.include_router(
    retrieval.router,
    prefix="/api",
    tags=["retrieval"]
)

app.include_router(
    health.router,
    prefix="/api",
    tags=["health"]
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "Ad Retrieval API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
