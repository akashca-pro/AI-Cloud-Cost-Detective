import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type ApiError } from "../lib/api";
import { ALL_SERVICES, type ServiceName } from "../types/analysis";

const SERVICE_LABELS: Record<ServiceName, string> = {
  ec2: "EC2",
  rds: "RDS",
  s3: "S3",
  elb: "ELB",
  ebs: "EBS",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [regions, setRegions] = useState<string[]>([]);
  const [loadingRegions, setLoadingRegions] = useState(true);
  const [regionError, setRegionError] = useState<string | null>(null);

  const [allRegions, setAllRegions] = useState(true);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [selectedServices, setSelectedServices] = useState<ServiceName[]>([...ALL_SERVICES]);

  const [tagKey, setTagKey] = useState("");
  const [tagValue, setTagValue] = useState("");
  const [tags, setTags] = useState<Record<string, string>>({});

  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadRegions() {
      setLoadingRegions(true);
      setRegionError(null);
      try {
        const data = await api.getRegions();
        if (!cancelled) {
          setRegions(data.regions);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            typeof err === "object" && err && "message" in err
              ? String((err as ApiError).message)
              : "Failed to load AWS regions.";
          setRegionError(message);
        }
      } finally {
        if (!cancelled) {
          setLoadingRegions(false);
        }
      }
    }
    void loadRegions();
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleRegion(region: string) {
    setSelectedRegions((prev) =>
      prev.includes(region) ? prev.filter((r) => r !== region) : [...prev, region],
    );
  }

  function toggleService(service: ServiceName) {
    setSelectedServices((prev) =>
      prev.includes(service) ? prev.filter((s) => s !== service) : [...prev, service],
    );
  }

  function handleAddTag(event: FormEvent) {
    event.preventDefault();
    const key = tagKey.trim();
    const value = tagValue.trim();
    if (!key || !value) return;
    setTags((prev) => ({ ...prev, [key]: value }));
    setTagKey("");
    setTagValue("");
  }

  function removeTag(key: string) {
    setTags((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  async function handleRunAnalysis() {
    if (selectedServices.length === 0) {
      setRunError("Select at least one service.");
      return;
    }
    if (!allRegions && selectedRegions.length === 0) {
      setRunError("Select at least one region or choose all enabled regions.");
      return;
    }

    setRunning(true);
    setRunError(null);
    try {
      const result = await api.analyze({
        regions: allRegions ? null : selectedRegions,
        services: selectedServices,
        tags,
      });
      navigate("/report", { state: { result } });
    } catch (err) {
      const message =
        typeof err === "object" && err && "message" in err
          ? String((err as ApiError).message)
          : "Analysis failed. Please try again.";
      setRunError(message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-100">Run analysis</h1>
        <p className="mt-2 text-slate-400">
          Choose AWS scope, then scan for FinOps findings across your account.
        </p>
      </div>

      <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="mb-4 text-lg font-medium text-slate-200">Regions</h2>
        <label className="mb-4 flex cursor-pointer items-center gap-3 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={allRegions}
            onChange={(e) => setAllRegions(e.target.checked)}
            className="rounded border-slate-600 bg-slate-950 text-indigo-600"
          />
          All enabled regions (recommended)
        </label>

        {!allRegions && (
          <div>
            {loadingRegions ? (
              <p className="text-sm text-slate-500">Loading regions…</p>
            ) : regionError ? (
              <p className="rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
                {regionError}
              </p>
            ) : (
              <div className="grid max-h-48 grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3">
                {regions.map((region) => (
                  <label
                    key={region}
                    className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800/50"
                  >
                    <input
                      type="checkbox"
                      checked={selectedRegions.includes(region)}
                      onChange={() => toggleRegion(region)}
                      className="rounded border-slate-600 bg-slate-950 text-indigo-600"
                    />
                    {region}
                  </label>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="mb-4 text-lg font-medium text-slate-200">Services</h2>
        <div className="flex flex-wrap gap-3">
          {ALL_SERVICES.map((service) => (
            <label
              key={service}
              className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800/50"
            >
              <input
                type="checkbox"
                checked={selectedServices.includes(service)}
                onChange={() => toggleService(service)}
                className="rounded border-slate-600 bg-slate-950 text-indigo-600"
              />
              {SERVICE_LABELS[service]}
            </label>
          ))}
        </div>
      </section>

      <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="mb-1 text-lg font-medium text-slate-200">Tag filters</h2>
        <p className="mb-4 text-sm text-slate-500">Optional — resources must match all tags (AND).</p>

        <form onSubmit={handleAddTag} className="mb-4 flex flex-wrap gap-2">
          <input
            type="text"
            placeholder="Key (e.g. Environment)"
            value={tagKey}
            onChange={(e) => setTagKey(e.target.value)}
            className="min-w-[140px] flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            placeholder="Value (e.g. prod)"
            value={tagValue}
            onChange={(e) => setTagValue(e.target.value)}
            className="min-w-[140px] flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
          >
            Add tag
          </button>
        </form>

        {Object.keys(tags).length > 0 ? (
          <ul className="flex flex-wrap gap-2">
            {Object.entries(tags).map(([key, value]) => (
              <li
                key={key}
                className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-sm text-slate-300"
              >
                <span>
                  {key}=<span className="text-indigo-300">{value}</span>
                </span>
                <button
                  type="button"
                  onClick={() => removeTag(key)}
                  className="text-slate-500 hover:text-red-400"
                  aria-label={`Remove tag ${key}`}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-600">No tag filters — scan all matching resources.</p>
        )}
      </section>

      {runError && (
        <div className="mb-4 rounded-lg border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          {runError}
        </div>
      )}

      <button
        type="button"
        onClick={() => void handleRunAnalysis()}
        disabled={running || loadingRegions}
        className="w-full rounded-xl bg-indigo-600 px-6 py-3 text-base font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
      >
        {running ? "Running analysis…" : "Run analysis"}
      </button>
    </div>
  );
}
