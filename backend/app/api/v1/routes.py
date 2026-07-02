from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from ... import models, schemas
from ...database import get_db

router = APIRouter()

# --- 1. Project Management ---
@router.post("/projects", response_model=schemas.QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_project_and_queue(queue_in: schemas.QueueCreate, db: AsyncSession = Depends(get_db)):
    """
    For simplicity in this assignment, we will create a dummy User, 
    a Project, and a Queue all in one go so you can start submitting jobs immediately.
    """
    # 1. Create a dummy user (in a real app, this comes from authentication)
    new_user = models.User(email=f"admin_{uuid.uuid4().hex[:6]}@codity.ai", password_hash="hashed_pw")
    db.add(new_user)
    await db.flush() # Flush to get the new_user.id

    # 2. Create a project
    new_project = models.Project(owner_id=new_user.id, name="Default Assignment Project")
    db.add(new_project)
    await db.flush()

    # 3. Create the queue
    new_queue = models.Queue(
        project_id=new_project.id,
        name=queue_in.name,
        priority=queue_in.priority,
        concurrency_limit=queue_in.concurrency_limit
    )
    db.add(new_queue)
    await db.commit()
    await db.refresh(new_queue)
    
    return new_queue

# --- 2. Job Management (The Producer) ---
@router.post("/queues/{queue_id}/jobs", response_model=schemas.JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(queue_id: uuid.UUID, job_in: schemas.JobCreate, db: AsyncSession = Depends(get_db)):
    """
    Submit a new asynchronous job to a specific queue.
    """
    # Verify the queue exists
    result = await db.execute(select(models.Queue).where(models.Queue.id == queue_id))
    queue = result.scalars().first()
    
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # Create the job
    new_job = models.Job(
        queue_id=queue.id,
        payload=job_in.payload,
        scheduled_at=job_in.scheduled_at or models.utcnow(),
        max_retries=job_in.max_retries,
        retry_policy=job_in.retry_policy
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    return new_job

@router.get("/queues/{queue_id}/jobs", response_model=List[schemas.JobResponse])
async def list_jobs(queue_id: uuid.UUID, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Fetch all jobs in a specific queue to monitor their status.
    """
    result = await db.execute(
        select(models.Job)
        .where(models.Job.queue_id == queue_id)
        .order_by(models.Job.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()