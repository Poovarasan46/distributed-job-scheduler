"use client";

import {
  Activity,
  Server,
  Database,
  Layers,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useState, useEffect } from "react";
import axios from "axios";

// Define what a Job looks like based on our Python backend
interface Job {
  id: string;
  status: string;
  payload: any;
  created_at: string;
}

export default function DashboardOverview() {
  const [mounted, setMounted] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);

  // 👇 PASTE YOUR UUID FROM PGADMIN HERE 👇
  const QUEUE_ID = "22b06e8a-b956-4c2b-a010-a187c6eeaaa7";

  const [stats, setStats] = useState({
    activeWorkers: 1, // You can build a worker tracking API later!
    totalQueues: 1,
    jobsCompleted: 0,
    jobsFailed: 0,
  });

  useEffect(() => {
    // 1. Tell React the client has mounted to prevent Hydration Errors
    setMounted(true);

    // 2. Fetch live data from FastAPI
    const fetchJobs = async () => {
      if (QUEUE_ID === "YOUR_QUEUE_ID_HERE") return;

      try {
        const response = await axios.get(
          `http://127.0.0.1:8000/api/v1/queues/${QUEUE_ID}/jobs`,
        );
        const liveJobs = response.data;
        setJobs(liveJobs);

        // Dynamically calculate stats based on the database!
        const completed = liveJobs.filter(
          (j: Job) => j.status === "completed",
        ).length;
        const failed = liveJobs.filter(
          (j: Job) => j.status === "failed",
        ).length;

        setStats((prev) => ({
          ...prev,
          jobsCompleted: completed,
          jobsFailed: failed,
        }));
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
      }
    };

    // Fetch immediately on load
    fetchJobs();

    // 3. Set up polling for LIVE updates (Bonus feature requirement!)
    const interval = setInterval(fetchJobs, 2000); // Check for new jobs every 2 seconds
    return () => clearInterval(interval);
  }, []);

  // Prevent hydration mismatch by hiding the UI for a millisecond until the browser takes over
  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      {/* Header */}
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Activity className="text-blue-600 h-8 w-8" />
          Distributed Job Scheduler
        </h1>
        <p className="text-gray-500 mt-2">
          Production-grade task orchestration and monitoring.
        </p>
      </header>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Active Workers</p>
            <p className="text-3xl font-bold text-green-600 mt-1">
              {stats.activeWorkers}
            </p>
          </div>
          <div className="bg-green-100 p-3 rounded-lg">
            <Server className="h-6 w-6 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Active Queues</p>
            <p className="text-3xl font-bold text-blue-600 mt-1">
              {stats.totalQueues}
            </p>
          </div>
          <div className="bg-blue-100 p-3 rounded-lg">
            <Layers className="h-6 w-6 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">Completed Jobs</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {stats.jobsCompleted}
            </p>
          </div>
          <div className="bg-gray-100 p-3 rounded-lg">
            <CheckCircle className="h-6 w-6 text-gray-700" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">
              Failed (Dead Letter)
            </p>
            <p className="text-3xl font-bold text-red-600 mt-1">
              {stats.jobsFailed}
            </p>
          </div>
          <div className="bg-red-100 p-3 rounded-lg">
            <XCircle className="h-6 w-6 text-red-600" />
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Database className="h-5 w-5 text-gray-500" />
            Live Execution Logs
          </h2>
          <span className="text-xs font-medium bg-green-100 text-green-800 px-3 py-1 rounded-full animate-pulse">
            Live Polling Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 text-sm text-gray-500 border-b border-gray-200">
                <th className="p-4 font-medium">Job ID</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium">Payload</th>
                <th className="p-4 font-medium">Created At</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-gray-400">
                    No jobs found in this queue.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr
                    key={job.id}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <td className="p-4 font-mono text-xs text-gray-600">
                      {job.id.split("-")[0]}...
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium border ${
                          job.status === "completed"
                            ? "bg-green-50 text-green-700 border-green-200"
                            : job.status === "running"
                              ? "bg-blue-50 text-blue-700 border-blue-200"
                              : job.status === "failed"
                                ? "bg-red-50 text-red-700 border-red-200"
                                : "bg-gray-50 text-gray-700 border-gray-200"
                        }`}
                      >
                        {job.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-xs text-gray-500">
                      {JSON.stringify(job.payload)}
                    </td>
                    <td className="p-4 text-sm text-gray-600">
                      {new Date(job.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
