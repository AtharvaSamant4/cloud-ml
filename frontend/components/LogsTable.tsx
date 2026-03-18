"use client";

import { useEffect, useState } from "react";

export default function LogsTable() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/logs`);
      const data = await res.json();
      setLogs(data.logs || []);
    } catch (err) {
      console.error("Failed to fetch logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 mb-4">
      <div className="p-6 bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 shadow-2xl rounded-3xl animate-fade-in relative overflow-hidden">
        {/* Decorative subtle top border */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent"></div>
        
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
          <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-white flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse"></span>
            Live Prediction Logs
          </h2>
          <button
            onClick={fetchLogs}
            className="px-4 py-2 bg-indigo-500/10 text-indigo-300 font-medium rounded-xl hover:bg-indigo-500/20 transition-all border border-indigo-500/20 shadow-sm flex items-center gap-2 text-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            Sync Database
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center flex flex-col items-center gap-4">
            <svg className="animate-spin h-6 w-6 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <p className="text-slate-400 font-medium animate-pulse text-sm">Fetching telemetry from network...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="py-16 text-center bg-slate-800/30 rounded-2xl border border-dashed border-slate-700/50">
            <div className="w-12 h-12 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm text-slate-500">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" /></svg>
            </div>
            <p className="text-slate-400 font-medium">No live predictions have been routed yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-700/50 shadow-inner bg-slate-900/40">
            <table className="w-full text-sm text-left border-collapse">
              <thead className="text-xs text-slate-400 uppercase tracking-wider bg-slate-800/80 border-b border-slate-700/50 font-bold">
                <tr>
                  <th className="px-5 py-4 border-r border-slate-700/30">Time <span className="text-slate-600 font-normal ml-1">(Local)</span></th>
                  <th className="px-5 py-4 border-r border-slate-700/30 text-right">Limit Bal</th>
                  <th className="px-5 py-4 border-r border-slate-700/30 text-center">Age</th>
                  <th className="px-5 py-4 border-r border-slate-700/30 text-center">PAY_0</th>
                  <th className="px-5 py-4 border-r border-slate-700/30 text-right">Bill Amt</th>
                  <th className="px-5 py-4 border-r border-slate-700/30 text-right">Pay Amt</th>
                  <th className="px-5 py-4 text-center">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {logs.map((log, i) => (
                  <tr key={i} className="hover:bg-slate-700/30 transition-colors group">
                    <td className="px-5 py-4 text-slate-400 font-mono text-xs whitespace-nowrap border-r border-slate-700/30">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-right font-medium text-slate-300 border-r border-slate-700/30">
                      ${log.LIMIT_BAL?.toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-center text-slate-400 border-r border-slate-700/30">{log.AGE}</td>
                    <td className="px-5 py-4 text-center border-r border-slate-700/30">
                      <span className={`px-2 py-1 rounded bg-slate-800 text-xs font-mono border ${
                        log.PAY_0 > 0 ? "border-amber-500/30 text-amber-400" : "border-slate-700 text-slate-400"
                      }`}>{log.PAY_0}</span>
                    </td>
                    <td className="px-5 py-4 text-right text-slate-400 border-r border-slate-700/30">
                      ${log.BILL_AMT1?.toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-right text-slate-400 border-r border-slate-700/30">
                      ${log.PAY_AMT1?.toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span
                        className={`inline-flex items-center justify-center px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider shadow-sm ${
                          log.prediction === 1
                            ? "bg-red-500/10 text-red-400 border border-red-500/20"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        }`}
                      >
                        {log.prediction === 1 ? "High Risk" : "Low Risk"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
