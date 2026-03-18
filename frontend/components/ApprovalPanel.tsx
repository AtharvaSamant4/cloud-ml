"use client";

import { useEffect, useState } from "react";

export default function ApprovalPanel() {
  const [stagingData, setStagingData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const fetchStagingModel = async () => {
    try {
      const res = await fetch(`${API_URL}/staging-model`);
      const data = await res.json();
      if (data.status === "pending") {
        setStagingData(data.metrics);
      } else {
        setStagingData(null);
      }
    } catch (err) {
      console.error("Failed to fetch staging model", err);
    }
  };

  useEffect(() => {
    fetchStagingModel();
    // Poll every 30 seconds in case a background job finishes
    const interval = setInterval(fetchStagingModel, 30000);
    return () => clearInterval(interval);
  }, [API_URL]);

  const handleAction = async (endpoint: string) => {
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch(`${API_URL}/${endpoint}`, { method: "POST" });
      const data = await res.json();
      if (data.status === "approved" || data.status === "rejected") {
        setMessage(`Model successfully ${data.status}!`);
        setStagingData(null);
      } else {
        setMessage("Error processing model request.");
      }
    } catch (err) {
      console.error(`Failed to ${endpoint}`, err);
      setMessage("Network error occurred.");
    } finally {
      setLoading(false);
      // Clear message after 5 seconds
      if (endpoint === 'approve-model' || endpoint === 'reject-model') {
        setTimeout(() => setMessage(''), 5000);
      }
    }
  };

  if (!stagingData && !message) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 mb-4">
      {message && (
        <div className="p-4 mb-4 text-sm text-green-800 rounded-lg bg-green-50 border border-green-200 text-center font-medium">
          {message}
        </div>
      )}

      {stagingData && (
        <div className="p-6 bg-amber-50 rounded-2xl border-2 border-amber-200 shadow-lg animate-fade-in relative overflow-hidden">
          {/* Decorative warning stripes */}
          <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-amber-400 via-orange-400 to-amber-400"></div>
          
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                </span>
                <h2 className="text-xl font-bold text-amber-900">Action Required: New Model Staged</h2>
              </div>
              <p className="text-sm text-amber-800 mb-3">
                Concept drift was detected and a new Random Forest model was trained automatically by the background pipeline. It is awaiting human review.
              </p>
              
              <div className="inline-flex gap-4 p-3 bg-white/60 rounded-xl border border-amber-100/50">
                <div>
                  <p className="text-xs text-amber-600 font-semibold uppercase tracking-wider">New F1 Score</p>
                  <p className="text-2xl font-black text-amber-900">{(stagingData.f1_score * 100).toFixed(1)}%</p>
                </div>
                {/* Visual separator */}
                <div className="w-px bg-amber-200"></div>
                <div>
                  <p className="text-xs text-amber-600 font-semibold uppercase tracking-wider">Status</p>
                  <p className="text-lg font-bold text-amber-700 mt-1 capitalize">{stagingData.status.replace("_", " ")}</p>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3 w-full sm:w-auto shrink-0">
              <button
                onClick={() => handleAction("approve-model")}
                disabled={loading}
                className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? "Processing..." : "✓ Approve & Deploy"}
              </button>
              <button
                onClick={() => handleAction("reject-model")}
                disabled={loading}
                className="px-6 py-3 bg-white hover:bg-red-50 text-red-600 font-bold border-2 border-red-200 hover:border-red-300 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? "Processing..." : "✗ Reject Model"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
