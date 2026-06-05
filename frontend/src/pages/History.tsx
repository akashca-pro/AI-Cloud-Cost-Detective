import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ApiError } from "../lib/api";
import { formatAnalysisTimestamp } from "../lib/format";
import type { AnalysisHistoryItem } from "../types/analysis";

function historyLabel(item: AnalysisHistoryItem): string {
  return item.workload_label || item.regions_scanned.join(", ") || "AWS scan";
}

export default function History() {
  const [analyses, setAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getHistory(50);
        if (!cancelled) {
          setAnalyses(data.analyses);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            typeof err === "object" && err && "message" in err
              ? String((err as ApiError).message)
              : "Could not load analysis history.";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadHistory();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-100">Analysis history</h1>
        <p className="mt-2 text-slate-400">
          Past scans saved in the database. Open a report to view findings and fix commands.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        {loading ? (
          <p className="text-sm text-slate-500">Loading history…</p>
        ) : error ? (
          <p className="rounded-lg border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-200">
            {error}
          </p>
        ) : analyses.length === 0 ? (
          <p className="text-sm text-slate-600">
            No saved analyses yet.{" "}
            <Link to="/" className="text-indigo-400 hover:text-indigo-300">
              Run your first scan
            </Link>
            .
          </p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {analyses.map((item) => (
              <li key={item.id}>
                <Link
                  to={`/report/${item.id}`}
                  className="-mx-2 flex flex-wrap items-center justify-between gap-3 rounded-lg px-2 py-4 transition hover:bg-slate-800/30"
                >
                  <div>
                    <p className="font-medium text-slate-200">{historyLabel(item)}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.services_scanned.join(", ") || "—"}
                      {item.regions_scanned.length > 0 && ` · ${item.regions_scanned.join(", ")}`}
                    </p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-slate-300">{formatAnalysisTimestamp(item.created_at)}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.resources_scanned} resources · {item.issues_found} findings
                    </p>
                    {item.estimated_savings && (
                      <p className="mt-1 text-xs text-emerald-400/90">
                        Est. savings: {item.estimated_savings}
                      </p>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
