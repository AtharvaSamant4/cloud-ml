"use client";

import { useState } from "react";

/* ---------- minimal fields config ---------- */
const FIELDS = [
  {
    name: "LIMIT_BAL",
    label: "Credit Limit",
    placeholder: "e.g. 20000",
    tooltip: "Amount of given credit",
    type: "number",
    min: 10000,
    max: 1000000,
  },
  {
    name: "AGE",
    label: "Age",
    placeholder: "e.g. 30",
    tooltip: "Age of the applicant",
    type: "number",
    min: 18,
    max: 80,
  },
  {
    name: "PAY_0",
    label: "Recent Payment Status",
    placeholder: "-2 to 8",
    tooltip:
      "-2 = No consumption, -1 = Paid duly, 0 = Revolving credit, 1+ = Months delayed",
    helperText: "Repayment status (-2 = no delay, 0 = on time, 1+ = delay)",
    type: "number",
    min: -2,
    max: 8,
  },
  {
    name: "BILL_AMT1",
    label: "Recent Bill Amount",
    placeholder: "e.g. 5000",
    tooltip: "Amount of latest bill statement",
    type: "number",
    min: 0,
    max: 100000,
  },
  {
    name: "PAY_AMT1",
    label: "Recent Payment Amount",
    placeholder: "e.g. 2000",
    tooltip: "Amount paid in the latest month",
    type: "number",
    min: 0,
    max: 50000,
  },
];

export default function PredictionForm() {
  const [formData, setFormData] = useState<Record<string, string>>({
    LIMIT_BAL: "",
    AGE: "",
    PAY_0: "",
    BILL_AMT1: "",
    PAY_AMT1: "",
  });

  const [prediction, setPrediction] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Field Validation
  const getFieldError = (name: string, value: string) => {
    if (value === "") return null;

    const num = Number(value);
    const field = FIELDS.find((f) => f.name === name);

    if (!field) return null;
    if (isNaN(num)) return "Must be a valid number.";
    if (num < field.min) return `Minimum value is ${field.min.toLocaleString()}.`;
    if (num > field.max) return `Maximum value is ${field.max.toLocaleString()}.`;

    return null;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setApiError(null);
    setPrediction(null);
  };

  const handleReset = () => {
    setFormData({
      LIMIT_BAL: "",
      AGE: "",
      PAY_0: "",
      BILL_AMT1: "",
      PAY_AMT1: "",
    });
    setPrediction(null);
    setApiError(null);
  };

  const hasErrors = FIELDS.some((f) => getFieldError(f.name, formData[f.name]) !== null);
  const isComplete = FIELDS.every((f) => formData[f.name] !== "");
  const canSubmit = isComplete && !hasErrors;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setPrediction(null);
    setApiError(null);

    // Ensure all inputs are converted to numbers exactly as requested
    const data: Record<string, number> = {};
    for (const key of Object.keys(formData)) {
      data[key] = Number(formData[key]);
    }

    try {
      // Use deployed environment variable if available, fallback to local IPv4 for dev
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        // If it throws a 500 or 404, capture the text to debug easily
        const errorText = await response.text();
        throw new Error(`API returned ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      
      // Since your modified backend returns {"error": "..."} inside a 200 OK sometimes
      if (result.error) {
         throw new Error(result.error);
      }
      
      setPrediction(result.prediction);
      
    } catch (err: unknown) {
      console.error("Backend Error:", err);
      const msg = err instanceof Error ? err.message : "An unexpected network error occurred";
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      setApiError(`Could not fetch prediction. Make sure the API is running at ${API_URL}\n\nError: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="form-section pb-2">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {FIELDS.map((field) => {
            const errorMsg = getFieldError(field.name, formData[field.name]);
            return (
              <div key={field.name} className="group flex flex-col">
                <label
                  htmlFor={field.name}
                  className="field-label block mb-2"
                  title={field.tooltip}
                >
                  {field.label}
                </label>
                <input
                  id={field.name}
                  type={field.type}
                  name={field.name}
                  min={field.min}
                  max={field.max}
                  value={formData[field.name]}
                  onChange={handleChange}
                  placeholder={field.placeholder}
                  className={`form-input w-full px-4 py-2.5 rounded-xl text-sm transition-colors ${
                    errorMsg
                      ? "border-red-500/50 bg-red-500/5 focus:border-red-500/50"
                      : ""
                  }`}
                />
                
                <div className="min-h-[1.5rem] mt-1.5 flex flex-col justify-start">
                  {errorMsg ? (
                    <span className="text-xs font-semibold text-red-400 animate-fade-in">
                      {errorMsg}
                    </span>
                  ) : field.helperText ? (
                    <span className="text-xs text-slate-500">
                      {field.helperText}
                    </span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={!canSubmit || loading}
          className="btn-primary flex-1 py-3.5 px-6 rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group-hover:disabled:transform-none"
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>Predicting...</span>
            </>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="opacity-80">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Predict Risk
            </>
          )}
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="px-6 py-3.5 rounded-xl text-sm font-medium text-slate-400 bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:text-slate-300 transition-all duration-200"
        >
          Reset
        </button>
      </div>

      {apiError && (
        <div className="result-card result-danger rounded-xl p-4 mt-4 flex items-start gap-3 animate-fade-in">
          <div className="shrink-0 mt-0.5 text-red-400 text-lg">⚠️</div>
          <div>
            <p className="text-sm font-semibold text-red-400 mb-1">
              API Error
            </p>
            <p className="text-xs text-red-300/70 whitespace-pre-line leading-relaxed">
              {apiError}
            </p>
          </div>
        </div>
      )}

      {prediction !== null && (
        <div
          className={`result-card rounded-xl p-5 mt-4 flex items-center justify-between shadow-lg animate-fade-in ${
            prediction === 1 ? "result-danger" : "result-success"
          }`}
        >
          <div className="flex items-center gap-4">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center text-xl shrink-0 ${
                prediction === 1
                  ? "bg-red-500/20 text-red-400"
                  : "bg-emerald-500/20 text-emerald-400"
              }`}
            >
              {prediction === 1 ? "⚠" : "✓"}
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-0.5">
                Outcome
              </p>
              <p
                className={`text-xl font-bold tracking-tight ${
                  prediction === 1 ? "text-red-400" : "text-emerald-400"
                }`}
              >
                {prediction === 1 ? "High Risk of Default" : "Low Risk"}
              </p>
            </div>
          </div>
        </div>
      )}
    </form>
  );
}
