from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # Ensures models are registered with Base
from .api.v1 import routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create all tables in the database asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables successfully created/verified!")
    yield
    # Shutdown: Dispose of the database engine cleanly
    await engine.dispose()
    print("🛑 Database connection closed.")

app = FastAPI(
    title="Distributed Job Scheduler API",
    description="Production-ready asynchronous background task orchestrator.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.7:3000" # Your specific network IP from earlier!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1", tags=["Jobs & Queues"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "job-scheduler"}