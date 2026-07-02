# Distributed Job Scheduler

A production-ready, asynchronous task orchestration platform. This system decouples job submission from execution, providing atomic task management, fault tolerance, and real-time observability.

---

## 🎥 System Demo


https://github.com/user-attachments/assets/5b7a31fe-3869-4005-9321-0223c7b0ae7f


---

## 🏗 System Architecture & Component Breakdown

The system is designed with a decoupled, horizontally scalable architecture consisting of four main layers:

1. **API Layer (Producer)**
   - Built with FastAPI.
   - Exposes RESTful endpoints to accept new jobs and create isolated projects/queues.
   - Stores incoming jobs in the database with a default `queued` status.

2. **Database Layer (The Source of Truth)**
   - Powered by PostgreSQL.
   - Acts as the central state manager for all tasks, ensuring data persistence and tracking job lifecycles.

3. **Worker Layer (Consumer)**
   - A dedicated asynchronous worker service responsible for continuously monitoring the job queue, atomically reserving pending jobs, executing task payloads, applying configurable retry policies for failed executions, and updating job statuses throughout their lifecycle to ensure reliable and fault-tolerant processing.

4. **Presentation Layer (Observer)**
   - A Next.js front-end application.
   - Uses client-side polling to fetch real-time telemetry from the API, visualizing worker status, queue health, and execution logs without needing complex WebSocket connections.

---

## 🧠 Core Design Decisions

- **Atomic Queue Management via PostgreSQL** — Instead of using Redis for the queue, this project uses PostgreSQL to maintain strict ACID compliance for job states. By implementing row-level locking (`SELECT ... FOR UPDATE SKIP LOCKED`), the system guarantees that even if multiple concurrent workers are running, no two workers can ever claim the same job. This eliminates race conditions natively.
- **Decoupled Worker Daemon** — The job processing engine operates as an independent asynchronous worker service, isolated from the FastAPI application. This separation enables resource-intensive and long-running tasks to execute independently of the API server, preventing request-handling bottlenecks, improving system responsiveness, and allowing the application and worker layer to scale independently for greater reliability and throughput.
- **Pull-Based Observability** — The frontend utilizes efficient `useEffect` polling rather than WebSockets. This provides a "push-like" real-time feel for the user while keeping the deployment architecture and state management drastically simpler and more resilient.

---

## 🚀 Key Capabilities

| Capability | Description |
|---|---|
| **Atomic Job Processing** | Thread-safe task distribution across multiple nodes. |
| **Fault Tolerance** | Automated retry policies defined per-job (`max_retries`). Permanent failures are gracefully logged and routed to a Dead Letter Queue (DLQ) to prevent system blockage. |
| **Real-Time Observability** | Live telemetry, dynamically updating status badges (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`), and error tracking. |
| **Multi-Tenancy** | Supports isolated job queues via project-based partitioning, allowing different clients or environments to use the same infrastructure safely. |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | FastAPI (Python), SQLAlchemy (Async), Uvicorn |
| **Database** | PostgreSQL |
| **Worker Node** | Asynchronous Python Engine |
| **Frontend UI** | Next.js (React), Tailwind CSS v4, Lucide Icons, Axios |

---
## 📸 Screenshots

### Live Dashboard
Real-time worker, queue, and job telemetry via client-side polling.
<img width="1208" height="890" alt="dashboard" src="https://github.com/user-attachments/assets/76339cf0-9295-4328-8632-fd0218f2476d" />


### Database Monitoring (pgAdmin)
Live PostgreSQL activity — server sessions, transactions/sec, and I/O on the queue tables.
<img width="1476" height="770" alt="pgadmin" src="https://github.com/user-attachments/assets/7f4d0917-5c76-4f87-b8e2-368854be57d5" />


### API Reference (Swagger / OpenAPI)
Interactive documentation for all project, queue, and job endpoints.
<img width="1887" height="900" alt="api" src="https://github.com/user-attachments/assets/4569a9e8-d0d9-4a8b-923e-c3a041f0bc5f" />



## 📂 Repository Structure

```text
distributed-job-scheduler/
├── backend/                  
│   ├── app/
│   │   ├── main.py           # FastAPI entry point & CORS config
│   │   ├── routes.py         # API endpoints (projects, queues, jobs)
│   │   └── worker/
│   │       └── engine.py     
├── frontend/                 # Next.js Dashboard
│   ├── app/
│   │   ├── page.tsx          # Main dashboard
│   │   └── globals.css       
│   ├── package.json          
│   └── tailwind.config.js    
├── .env                      
├── .gitignore                
├── README.md                 
└── requirements.txt          # dependencies
```

---

## 🔒 Security Configuration

To prevent exposing sensitive data (such as local IP addresses or database passwords) to version control, the system relies on environment variables.

1. Ensure `.env` is listed inside your `.gitignore` file.
2. Create a `.env` file in the root directory:

```env
# .env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
DATABASE_URL=postgresql://<YOUR_DB_USER>:<YOUR_DB_PASSWORD>@localhost:5432/<YOUR_DB_NAME>
```

---

## ⚙️ Step-by-Step Execution Guide

To run this project locally, start the components in the following sequence.

### 1. Start the PostgreSQL Database

Ensure your local PostgreSQL service (or Docker container) is running and accessible via the credentials provided in your `.env` file.

### 2. Start the Backend API (Terminal 1)

Boot up the "brain" of the application to accept jobs.

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn backend.app.main:app --reload
```

> API documentation available at: `http://127.0.0.1:8000/docs`

### 3. Start the Worker Daemon (Terminal 2)

Boot up the "muscle" that processes the jobs.

```bash
# Ensure the virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the worker engine
python -m backend.app.worker.engine
```

### 4. Start the Frontend Dashboard (Terminal 3)

Boot up the visual observer.

```bash
cd frontend
npm install
npm run dev
```

> Dashboard available at: `http://localhost:3000`

---

## 🧪 Quality Assurance & Testing Guide

Once the system is running, use the Swagger UI (`http://127.0.0.1:8000/docs`) to test the core features.

### Test 1: The Happy Path (Standard Execution)

1. Execute `POST /api/v1/queues/{queue_id}/jobs` using your primary queue ID.
2. **Verification:** The terminal running the Worker will output `📦 Claimed Job...` followed by `✅ Job finished`. The Next.js dashboard will update in real time from `QUEUED` to `COMPLETED`.

### Test 2: Multi-Tenancy (Scaling)

1. Execute `POST /api/v1/projects` with a custom project name in the request body.
2. Copy the newly generated `queue_id` from the response.
3. Submit a new job using that specific `queue_id`.
4. **Verification:** The system successfully isolates and processes tasks across different logical queues.

### Test 3: Fault Tolerance & Dead Letter Queue (DLQ)

1. Temporarily modify `backend/app/worker/engine.py` to force an error:

   ```python
   async def execute_job(payload: dict):
       raise Exception("Simulated fatal task failure!")
   ```

2. Restart the Worker Daemon terminal.
3. Submit a new job via Swagger, explicitly setting `"max_retries": 0` in the JSON request body.
4. **Verification:** The Worker will catch the exception without crashing. The job will immediately route to the Dead Letter Queue, and the Dashboard status badge will turn red, displaying `FAILED`.
   *(Remember to revert the forced error in your code after testing.)*

---

## 📄 License

This project is available for use under the terms of your choice — add a `LICENSE` file to formalize this (e.g., MIT, Apache 2.0).
