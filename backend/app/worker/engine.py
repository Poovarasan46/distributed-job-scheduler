import asyncio
import uuid
import socket
import json
import traceback
from datetime import datetime, timezone, timedelta
from sqlalchemy.sql import text
from ..database import AsyncSessionLocal

# Generate a unique ID and get the computer name for this specific worker instance
WORKER_ID = str(uuid.uuid4())
HOSTNAME = socket.gethostname()

async def register_worker():
    """Registers the worker in the database so we can monitor system health."""
    async with AsyncSessionLocal() as db:
        stmt = text("""
            INSERT INTO workers (id, hostname, status, last_heartbeat)
            VALUES (:id, :hostname, 'active', NOW())
            ON CONFLICT (id) DO UPDATE SET last_heartbeat = NOW()
        """)
        await db.execute(stmt, {"id": WORKER_ID, "hostname": HOSTNAME})
        await db.commit()

async def send_heartbeat():
    """Periodically tells the database this worker is still alive."""
    while True:
        await asyncio.sleep(10) # Send heartbeat every 10 seconds
        async with AsyncSessionLocal() as db:
            stmt = text("UPDATE workers SET last_heartbeat = NOW() WHERE id = :id")
            await db.execute(stmt, {"id": WORKER_ID})
            await db.commit()

async def execute_job(payload: dict):
    """
    Simulates actual work. In a real system, this would trigger emails, 
    process video files, or hit external APIs.
    """
    print(f"      ⚙️ Executing payload: {json.dumps(payload)}")
    await asyncio.sleep(3) # Simulate a 3-second task
    
    # Simulate a random failure to test your retry logic (optional)
    # import random
    # if random.choice([True, False]):
    #     raise Exception("Simulated network timeout!")

async def process_jobs():
    """The main polling loop that atomically claims and runs jobs."""
    print(f"🚀 Worker {WORKER_ID[:8]} started on {HOSTNAME}. Waiting for jobs...")
    
    while True:
        async with AsyncSessionLocal() as db:
            try:
                # 1. ATOMICALLY CLAIM A JOB
                claim_stmt = text("""
                    UPDATE jobs 
                    SET status = 'claimed', updated_at = NOW()
                    WHERE id = (
                        SELECT id FROM jobs 
                        WHERE status = 'queued' AND scheduled_at <= NOW()
                        ORDER BY scheduled_at ASC 
                        LIMIT 1 
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING id, payload, max_retries, retry_count, retry_policy;
                """)
                
                result = await db.execute(claim_stmt)
                job = result.mappings().first()
                await db.commit() # Commit the lock release

                if not job:
                    # No jobs available, sleep briefly to prevent CPU spike
                    await asyncio.sleep(2)
                    continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📦 Claimed Job: {job['id']}")

                # 2. CREATE EXECUTION RECORD
                exec_id = str(uuid.uuid4())
                exec_stmt = text("""
                    INSERT INTO job_executions (id, job_id, worker_id, status, started_at)
                    VALUES (:id, :job_id, :worker_id, 'running', NOW())
                """)
                await db.execute(exec_stmt, {"id": exec_id, "job_id": job['id'], "worker_id": WORKER_ID})
                await db.commit()

                # 3. EXECUTE THE WORK
                error_log = None
                job_success = False
                try:
                    await execute_job(job['payload'])
                    job_success = True
                except Exception as e:
                    error_log = traceback.format_exc()
                    print(f"      ❌ Job Failed: {str(e)}")

                # 4. HANDLE SUCCESS OR RETRY/FAILURE
                if job_success:
                    # Mark Job & Execution as Completed
                    await db.execute(text("UPDATE jobs SET status = 'completed', updated_at = NOW() WHERE id = :id"), {"id": job['id']})
                    await db.execute(text("UPDATE job_executions SET status = 'completed', completed_at = NOW() WHERE id = :id"), {"id": exec_id})
                else:
                    new_retry_count = job['retry_count'] + 1
                    
                    if new_retry_count >= job['max_retries']:
                        # Permanent Failure (Dead Letter)
                        await db.execute(text("UPDATE jobs SET status = 'failed', updated_at = NOW() WHERE id = :id"), {"id": job['id']})
                    else:
                        # Calculate backoff (e.g., exponential: 2^retries * 5 seconds)
                        delay_seconds = (2 ** new_retry_count) * 5
                        next_run = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
                        
                        await db.execute(text("""
                            UPDATE jobs 
                            SET status = 'queued', retry_count = :rc, scheduled_at = :next_run, updated_at = NOW() 
                            WHERE id = :id
                        """), {"rc": new_retry_count, "next_run": next_run, "id": job['id']})
                        print(f"      🔄 Job re-queued for retry at {next_run.strftime('%H:%M:%S')}")

                    # Log the execution failure
                    await db.execute(text("""
                        UPDATE job_executions 
                        SET status = 'failed', completed_at = NOW(), error_log = :error 
                        WHERE id = :id
                    """), {"error": error_log, "id": exec_id})

                await db.commit()
                print(f"      ✅ Job {job['id']} finished processing.")

            except Exception as e:
                print(f"Worker critical error: {e}")
                await db.rollback()
                await asyncio.sleep(5)

async def main():
    await register_worker()
    
    # Run the heartbeat and the job processor concurrently
    await asyncio.gather(
        send_heartbeat(),
        process_jobs()
    )

if __name__ == "__main__":
    # Windows-specific fix for asyncio loops
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Worker gracefully shutting down...")