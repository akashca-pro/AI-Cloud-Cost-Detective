import {
  getStepMessage,
  getStepState,
  PROGRESS_STEP_LABELS,
  PROGRESS_STEPS,
} from "../lib/progress";
import type { ProgressEvent } from "../types/analysis";

interface ProgressTrackerProps {
  events: ProgressEvent[];
  running: boolean;
}

function StepIcon({ state }: { state: ReturnType<typeof getStepState> }) {
  if (state === "complete") {
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
        ✓
      </span>
    );
  }
  if (state === "error") {
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-500/20 text-red-400">
        !
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className="relative flex h-6 w-6 items-center justify-center">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400/30" />
        <span className="relative h-2.5 w-2.5 rounded-full bg-indigo-400" />
      </span>
    );
  }
  return <span className="h-6 w-6 rounded-full border border-slate-700 bg-slate-900" />;
}

export default function ProgressTracker({ events, running }: ProgressTrackerProps) {
  if (!running && events.length === 0) {
    return null;
  }

  const errorEvent = events.find((event) => event.step === "error");

  return (
    <section
      className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/50 p-6"
      aria-live="polite"
      aria-busy={running}
    >
      <h2 className="mb-4 text-lg font-medium text-slate-200">Analysis progress</h2>

      <ol className="space-y-4">
        {PROGRESS_STEPS.map((step) => {
          const state = getStepState(step, events);
          const message = getStepMessage(step, events);
          const isActive = state === "active";

          return (
            <li key={step} className="flex gap-3">
              <div className="pt-0.5">
                <StepIcon state={state} />
              </div>
              <div className="min-w-0 flex-1">
                <p
                  className={[
                    "text-sm font-medium",
                    state === "complete"
                      ? "text-emerald-300"
                      : state === "error"
                        ? "text-red-300"
                        : isActive
                          ? "text-indigo-300"
                          : state === "pending"
                            ? "text-slate-500"
                            : "text-slate-300",
                  ].join(" ")}
                >
                  {PROGRESS_STEP_LABELS[step]}
                </p>
                {message && (
                  <p className="mt-1 text-sm text-slate-400">{message}</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>

      {errorEvent && (
        <p className="mt-4 rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {errorEvent.message}
        </p>
      )}
    </section>
  );
}
