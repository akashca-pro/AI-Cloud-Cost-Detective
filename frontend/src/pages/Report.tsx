import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, type ApiError } from "../lib/api";
import { formatAnalysisTimestamp } from "../lib/format";
import type { AnalyzeResponse, Finding, Severity } from "../types/analysis";

interface ReportLocationState {
  result?: AnalyzeResponse;
  analyzedAt?: string | null;
}

function SeverityBadge({ severity }: { severity: Severity }) {
  const styles: Record<Severity, string> = {
    high: "border-red-800 bg-red-950/60 text-red-300",
    medium: "border-amber-800 bg-amber-950/60 text-amber-300",
    low: "border-slate-700 bg-slate-800/80 text-slate-300",
  };
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide ${styles[severity]}`}
    >
      {severity}
    </span>
  );
}

function CopyButton({ text, label = "Copy fix" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      onClick={() => void handleCopy()}
      className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-slate-800"
    >
      {copied ? "Copied!" : label}
    </button>
  );
}

function FindingCard({
  finding,
  fixCommand,
  aiExplanation,
}: {
  finding: Finding;
  fixCommand?: string | null;
  aiExplanation?: string | null;
}) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <SeverityBadge severity={finding.severity} />
        <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
          {finding.category}
        </span>
        <span className="text-xs text-slate-500">
          {finding.resource_type} · {finding.region}
        </span>
      </div>

      <h3 className="text-lg font-medium text-slate-100">{finding.title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">{finding.description}</p>

      {finding.recommendation_hint && (
        <p className="mt-3 text-sm text-slate-300">
          <span className="font-medium text-slate-200">Hint:</span> {finding.recommendation_hint}
        </p>
      )}

      {aiExplanation && (
        <p className="mt-3 rounded-lg border border-indigo-900/50 bg-indigo-950/30 px-3 py-2 text-sm text-indigo-200">
          {aiExplanation}
        </p>
      )}

      {fixCommand && (
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Fix command
            </span>
            <CopyButton text={fixCommand} />
          </div>
          <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs text-emerald-300">
            {fixCommand}
          </pre>
        </div>
      )}
    </article>
  );
}

export default function Report() {
  const { analysisId } = useParams<{ analysisId?: string }>();
  const location = useLocation();
  const state = location.state as ReportLocationState | null;

  const [result, setResult] = useState<AnalyzeResponse | null>(state?.result ?? null);
  const [analyzedAt, setAnalyzedAt] = useState<string | null>(state?.analyzedAt ?? null);
  const [displayAnalysisId, setDisplayAnalysisId] = useState<string | null>(
    state?.result?.analysis_id ?? analysisId ?? null,
  );
  const [loading, setLoading] = useState(Boolean(analysisId && !state?.result));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId || state?.result) return;

    const id = analysisId;
    let cancelled = false;
    async function loadHistory() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getHistoryDetail(id);
        if (!cancelled) {
          setResult(data.analysis.analysis_result ?? null);
          setAnalyzedAt(data.analysis.created_at ?? null);
          setDisplayAnalysisId(data.analysis.id);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            typeof err === "object" && err && "message" in err
              ? String((err as ApiError).message)
              : "Failed to load report.";
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
  }, [analysisId, state?.result]);

  const enrichmentByFindingId = useMemo(() => {
    const map = new Map<string, { fix_command?: string | null; ai_explanation?: string | null }>();
    for (const item of result?.ai_enrichment?.enriched_findings ?? []) {
      map.set(item.finding_id, item);
    }
    return map;
  }, [result]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-center text-slate-400">
        Loading report…
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p className="rounded-lg border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          {error ?? "No report data. Run an analysis from the dashboard."}
        </p>
        <Link
          to="/"
          className="mt-4 inline-block text-sm text-indigo-400 hover:text-indigo-300"
        >
          ← Back to dashboard
        </Link>
      </div>
    );
  }

  const ai = result.ai_enrichment;
  const totalFindings = result.findings.length;

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/" className="text-sm text-indigo-400 hover:text-indigo-300">
            ← Dashboard
          </Link>
          <h1 className="mt-2 text-3xl font-semibold text-slate-100">Analysis report</h1>
          {displayAnalysisId && (
            <p className="mt-1 font-mono text-xs text-slate-500">{displayAnalysisId}</p>
          )}
          {analyzedAt && (
            <p className="mt-2 text-sm text-slate-400">
              Analyzed {formatAnalysisTimestamp(analyzedAt)}
            </p>
          )}
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 text-right text-sm">
          <div className="text-slate-400">
            <span className="text-2xl font-semibold text-slate-100">{result.resource_count}</span>{" "}
            resources
          </div>
          <div className="text-slate-400">
            <span className="text-2xl font-semibold text-amber-300">{totalFindings}</span> findings
          </div>
        </div>
      </div>

      <section className="mb-8 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-xs font-medium uppercase tracking-wide text-slate-500">Scope</h2>
          <p className="mt-2 text-sm text-slate-300">
            Regions: {result.regions_scanned.join(", ") || "—"}
          </p>
          <p className="mt-1 text-sm text-slate-300">
            Services: {result.services_scanned.join(", ") || "—"}
          </p>
          {Object.keys(result.tags_filter).length > 0 && (
            <p className="mt-1 text-sm text-slate-300">
              Tags:{" "}
              {Object.entries(result.tags_filter)
                .map(([k, v]) => `${k}=${v}`)
                .join(", ")}
            </p>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-xs font-medium uppercase tracking-wide text-slate-500">
            AI summary
          </h2>
          {ai && !ai.skipped ? (
            <>
              <p className="mt-2 text-sm text-slate-300">{ai.summary || "No summary returned."}</p>
              {ai.estimated_savings && (
                <p className="mt-2 text-sm font-medium text-emerald-400">
                  Est. savings: {ai.estimated_savings}
                </p>
              )}
            </>
          ) : (
            <p className="mt-2 text-sm text-slate-500">
              {ai?.skip_reason ?? "AI enrichment was not available for this run."}
            </p>
          )}
        </div>
      </section>

      {totalFindings === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-8 text-center text-slate-400">
          No FinOps findings for this scan scope.
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-lg font-medium text-slate-200">Findings</h2>
          {result.findings.map((finding) => {
            const enriched = enrichmentByFindingId.get(finding.finding_id);
            return (
              <FindingCard
                key={finding.finding_id}
                finding={finding}
                fixCommand={enriched?.fix_command}
                aiExplanation={enriched?.ai_explanation}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
