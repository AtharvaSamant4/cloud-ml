import PredictionForm from "@/components/PredictionForm";
import LogsTable from "@/components/LogsTable";
import Link from "next/link";

export default function Home() {
  return (
    <>
      <div className="bg-mesh" />

      {/* Secure Admin Portal Link */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-8 z-50 animate-fade-in" style={{ animationDelay: "300ms" }}>
        <Link 
          href="/admin" 
          className="px-4 py-2 rounded-xl bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 text-slate-400 text-xs font-bold uppercase tracking-widest hover:bg-slate-800 hover:text-indigo-300 hover:border-indigo-500/30 transition-all shadow-lg flex items-center gap-2 group"
        >
          <span className="opacity-70 group-hover:opacity-100 transition-opacity">🔒</span> 
          <span>Admin Portal</span>
        </Link>
      </div>

      <main className="relative z-10 min-h-screen flex flex-col items-center px-4 py-10 sm:py-16">
        <header className="text-center mb-8 sm:mb-10 animate-fade-in max-w-xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/15 text-indigo-400 text-[0.68rem] font-semibold tracking-wider uppercase mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            ML-Powered Analysis
          </div>

          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-3">
            Credit Risk{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">
              Prediction System
            </span>
          </h1>

          <p className="text-sm text-slate-500 leading-relaxed max-w-md mx-auto">
            Assess credit card default probability using a RandomForest model
            trained on 30,000+ historical records.
          </p>
        </header>

        <div className="w-full max-w-2xl glass-card rounded-2xl p-6 sm:p-8 animate-fade-in"
             style={{ animationDelay: "150ms" }}>
          <PredictionForm />
        </div>

        <div className="w-full max-w-4xl animate-fade-in mt-12" style={{ animationDelay: "200ms" }}>
          <LogsTable />
        </div>

        {/* ── Footer ── */}
        <footer className="mt-10 text-center text-xs text-slate-600 animate-fade-in"
                style={{ animationDelay: "300ms" }}>
          <div className="flex items-center justify-center gap-2">
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>Cloud-ML Pipeline</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>FastAPI Backend</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>MLflow Tracked</span>
          </div>
        </footer>
      </main>
    </>
  );
}
