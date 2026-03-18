"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ApprovalPanel from "@/components/ApprovalPanel";

export default function AdminLabelingDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  
  const [unlabeledData, setUnlabeledData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Extremely basic auth for portfolio demo purposes
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === "admin123") {
      setIsAuthenticated(true);
      fetchUnlabeled();
    } else {
      alert("Invalid admin password. Try 'admin123'");
    }
  };

  const fetchUnlabeled = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/unlabeled-predictions`);
      const data = await res.json();
      setUnlabeledData(data.logs || []);
    } catch (err) {
      console.error("Failed to fetch unlabeled rows", err);
      setMessage("Failed to connect to backend database.");
    } finally {
      setLoading(false);
    }
  };

  const submitLabel = async (rowId: number, label: number) => {
    try {
      const res = await fetch(`${API_URL}/update-ground-truth/${rowId}?actual_label=${label}`, { 
        method: "POST" 
      });
      const data = await res.json();
      
      if (data.status === "success") {
        // Remove the row from the UI natively
        setUnlabeledData(prev => prev.filter(row => row.id !== rowId));
        setMessage(`Successfully marked Row #${rowId} as ${label === 1 ? 'Defaulted' : 'Paid'}`);
        setTimeout(() => setMessage(""), 3000);
      } else {
        alert("Failed: " + data.error);
      }
    } catch (err) {
      console.error(err);
      alert("Network error while updating ground truth.");
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-600/20 blur-[120px]" />
          <div className="absolute top-[60%] -right-[10%] w-[40%] h-[60%] rounded-full bg-violet-600/20 blur-[120px]" />
          <div className="absolute bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 w-full h-full mix-blend-overlay"></div>
        </div>

        <form onSubmit={handleLogin} className="relative z-10 bg-slate-800/60 backdrop-blur-xl border border-slate-700/50 p-8 sm:p-10 rounded-3xl shadow-2xl max-w-md w-full text-center animate-fade-in">
          <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-violet-600 shadow-inner rounded-2xl flex items-center justify-center mx-auto mb-6 transform rotate-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 text-white transform -rotate-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.956 11.956 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          
          <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-white">
            MLOps Portal
          </h1>
          <p className="text-sm text-slate-400 mb-8 font-medium tracking-wide">
            Restricted Ground-Truth Access Gate
          </p>
          
          <div className="relative mb-6 text-left">
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ml-1">Admin Passkey</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-5 py-4 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-400 transition-all font-mono"
            />
          </div>
          
          <button type="submit" className="w-full bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-indigo-500/25 active:scale-[0.98]">
            Authenticate Interface
          </button>
          
          <div className="mt-8 pt-6 border-t border-slate-700/50 text-center">
             <Link href="/" className="text-sm font-medium text-slate-400 hover:text-indigo-300 transition-colors inline-flex items-center gap-2">
               <span>←</span> Return to Public Application
             </Link>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 relative overflow-hidden p-4 sm:p-10 font-sans">
      {/* Background Ambience */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-violet-900/20 blur-[120px]" />
        <div className="absolute bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 w-full h-full mix-blend-overlay"></div>
      </div>

      <div className="max-w-6xl mx-auto relative z-10">
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 bg-slate-800/50 backdrop-blur-xl p-6 rounded-3xl shadow-lg border border-slate-700/50">
          <div>
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 to-white">
              Ground-Truth Labeller
            </h1>
            <p className="text-slate-400 text-sm mt-1 font-medium tracking-wide">
              Verify real-world outcomes to train the next-generation algorithm.
            </p>
          </div>
          <Link href="/" className="mt-4 sm:mt-0 px-5 py-2.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-bold border border-slate-600/50 transition-all shadow-sm">
            Exit Secure Terminal
          </Link>
        </header>

        {message && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-3 rounded-xl mb-6 font-medium animate-fade-in text-center shadow-lg backdrop-blur-sm">
            {message}
          </div>
        )}

        <div className="mb-8">
          <ApprovalPanel />
        </div>

        <div className="bg-slate-800/40 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden border border-slate-700/50">
          <div className="p-6 border-b border-slate-700/50 flex flex-col sm:flex-row justify-between items-start sm:items-center bg-slate-800/30">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
              Pending Clarifications ({unlabeledData.length})
            </h2>
            <button 
              onClick={fetchUnlabeled}
              className="mt-4 sm:mt-0 text-sm text-indigo-400 font-bold hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 px-4 py-2 rounded-xl transition-all border border-indigo-500/20 shadow-sm flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Refresh Database
            </button>
          </div>

          {loading ? (
            <div className="p-16 text-center text-indigo-400 font-medium animate-pulse flex flex-col items-center justify-center gap-4">
              <svg className="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Scanning Neon Clusters...
            </div>
          ) : unlabeledData.length === 0 ? (
            <div className="p-20 text-center">
              <div className="w-20 h-20 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-200 mb-2">All Caught Up!</h3>
              <p className="text-slate-400 font-medium tracking-wide">There are no pending unverified ML predictions natively in the system.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead className="bg-slate-800/80 text-slate-400 uppercase text-xs font-bold border-b border-slate-700/50 tracking-wider">
                  <tr>
                    <th className="px-6 py-5 rounded-tl-xl border-r border-slate-700/30">ID / Time</th>
                    <th className="px-6 py-5 border-r border-slate-700/30 text-right">Limit Bal</th>
                    <th className="px-6 py-5 border-r border-slate-700/30 text-center">Age</th>
                    <th className="px-6 py-5 border-r border-slate-700/30 text-center">Bot Prediction</th>
                    <th className="px-6 py-5 rounded-tr-xl text-center">Verify Actual Truth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {unlabeledData.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-700/30 transition-colors group">
                      <td className="px-6 py-5 whitespace-nowrap border-r border-slate-700/30">
                        <div className="font-bold text-slate-200 text-base">#{row.id}</div>
                        <div className="text-xs text-slate-500 font-mono mt-1">{new Date(row.timestamp).toLocaleString()}</div>
                      </td>
                      <td className="px-6 py-5 text-right font-medium text-slate-300 border-r border-slate-700/30">${row.LIMIT_BAL?.toLocaleString()}</td>
                      <td className="px-6 py-5 text-center text-slate-400 font-medium border-r border-slate-700/30">{row.AGE}</td>
                      <td className="px-6 py-5 text-center border-r border-slate-700/30">
                        <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider shadow-sm ${
                          row.prediction === 1 
                            ? 'bg-red-500/10 text-red-400 border border-red-500/20' 
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {row.prediction === 1 ? "High Risk" : "Low Risk"}
                        </span>
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex items-center justify-center gap-3">
                          <button 
                            onClick={() => submitLabel(row.id, 0)}
                            className="px-5 py-2.5 bg-slate-800 hover:bg-emerald-600 hover:text-white text-emerald-400 font-bold border border-emerald-500/30 rounded-xl transition-all shadow-sm hover:shadow-emerald-500/25 active:scale-95"
                          >
                            Paid (0)
                          </button>
                          <button 
                            onClick={() => submitLabel(row.id, 1)}
                            className="px-5 py-2.5 bg-slate-800 hover:bg-red-500 hover:text-white text-red-400 font-bold border border-red-500/30 rounded-xl transition-all shadow-sm hover:shadow-red-500/25 active:scale-95"
                          >
                            Default (1)
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
