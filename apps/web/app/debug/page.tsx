"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient, ApiError } from "@/lib/api-client";

interface HealthResponse {
  status: string;
}

export default function DebugPage() {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [testErrorResult, setTestErrorResult] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<HealthResponse>("/health");
      setHealthData(data);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`ApiError ${err.status}: ${err.serverMessage}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unknown error occurred");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    async function load() {
      try {
        const data = await apiClient.get<HealthResponse>("/health");
        if (!ignore) {
          setHealthData(data);
          setError(null);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (!ignore) {
          if (err instanceof ApiError) {
            setError(`ApiError ${err.status}: ${err.serverMessage}`);
          } else if (err instanceof Error) {
            setError(err.message);
          } else {
            setError("Unknown error occurred");
          }
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      ignore = true;
    };
  }, []);

  const triggerTestError = async () => {
    setTestErrorResult("Testing intentional 404 endpoint...");
    try {
      await apiClient.get("/non-existent-endpoint-test");
      setTestErrorResult("Unexpected success (should have failed)");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setTestErrorResult(
          `Caught ApiError -> Status: ${err.status}, Message: "${err.serverMessage}"`,
        );
      } else if (err instanceof Error) {
        setTestErrorResult(`Caught generic Error: ${err.message}`);
      }
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-2xl mx-auto space-y-6">
        <header className="border-b border-slate-800 pb-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              WareFlow — Debug & Handshake Probe
            </h1>
            <span className="text-xs px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
              Temporary (Phase 1)
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Verifying web-to-api CORS communication and typed API client integration.
          </p>
        </header>

        {/* Live /health Probe Card */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-200">FastAPI /health Status</h2>
            <button
              onClick={() => void fetchHealth()}
              disabled={loading}
              className="text-xs px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium transition"
            >
              {loading ? "Checking..." : "Re-check"}
            </button>
          </div>

          {loading && (
            <div className="flex items-center space-x-2 text-slate-400 text-sm">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              <span>Pinging FastAPI backend...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-950/50 border border-red-800/60 rounded-lg p-4 text-red-300 text-sm">
              <p className="font-medium">Connection Failed</p>
              <p className="text-xs text-red-400 mt-1">{error}</p>
            </div>
          )}

          {healthData && !loading && (
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
                </span>
                <span className="text-sm font-semibold text-emerald-400">
                  Status: {healthData.status}
                </span>
              </div>
              <div className="bg-slate-950 rounded-lg p-3 font-mono text-xs text-slate-300 border border-slate-800">
                <pre>{JSON.stringify(healthData, null, 2)}</pre>
              </div>
            </div>
          )}
        </section>

        {/* ApiError Verification Card */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-slate-200">ApiError Contract Test</h2>
            <button
              onClick={() => void triggerTestError()}
              className="text-xs px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition border border-slate-700"
            >
              Test Error Handling
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Trigger a 404 to verify that ApiError correctly surfaces HTTP status and server details.
          </p>

          {testErrorResult && (
            <div className="bg-slate-950 rounded-lg p-3 font-mono text-xs text-amber-300 border border-slate-800">
              {testErrorResult}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
