import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Dynamically find the backend directory and load the .env file
# __file__ is database.py -> parent is app/ -> parent.parent is backend/
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(f"DATABASE_URL environment variable is missing! Checked path: {env_path}")

# Create the async engine with an optimal connection pool size
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True if you want to inspect raw SQL queries in your console
    pool_size=20,
    max_overflow=10,
)

# Create an automated session factory for incoming requests/worker cycles
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Dependency injector to yield database sessions safely to routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()