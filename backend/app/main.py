from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.kafka import (
    init_kafka_producer,
    close_kafka_producer,
    start_kafka_consumers,
    stop_kafka_consumers
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_kafka_producer()
    await start_kafka_consumers()
    yield
    # Shutdown
    await stop_kafka_consumers()
    await close_kafka_producer()

app = FastAPI(
    title="AegisAI Backend Platform",
    description="Minimal entrypoint for AegisAI local service validation",
    version="0.1.0",
    lifespan=lifespan
)

# Expose Prometheus metric endpoint
Instrumentator().instrument(app).expose(app)

# Set up CORS middleware to allow cross-origin requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central routers
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["Health"])
async def health_check():
    """Verify backend server connectivity."""
    return {
        "status": "healthy",
        "service": "AegisAI Backend"
    }
