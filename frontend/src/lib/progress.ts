import type { ProgressEvent, ProgressStep } from "../types/analysis";

const STEP_ORDER: ProgressStep[] = ["fetching", "scanning", "ai", "storing", "complete"];

/** WebSocket URL for live analysis progress (backend on port 8000 in dev). */
export function getProgressWebSocketUrl(analysisId: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = import.meta.env.DEV ? "localhost:8000" : window.location.host;
  return `${protocol}//${host}/ws/progress/${analysisId}`;
}

export function openProgressSocket(
  analysisId: string,
  onEvent: (event: ProgressEvent) => void,
): Promise<WebSocket> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(getProgressWebSocketUrl(analysisId));

    ws.onopen = () => resolve(ws);
    ws.onerror = () => reject(new Error("WebSocket connection failed"));
    ws.onmessage = (message) => {
      try {
        onEvent(JSON.parse(message.data as string) as ProgressEvent);
      } catch {
        // Ignore malformed frames
      }
    };
  });
}

export function upsertProgressEvent(
  events: ProgressEvent[],
  incoming: ProgressEvent,
): ProgressEvent[] {
  const withoutStep = events.filter((event) => event.step !== incoming.step);
  return [...withoutStep, incoming];
}

export function getStepState(
  step: ProgressStep,
  events: ProgressEvent[],
): "pending" | "active" | "complete" | "error" {
  const event = events.find((item) => item.step === step);
  if (event?.status === "error" || event?.step === "error") return "error";
  if (event?.status === "complete") return "complete";
  if (event?.status === "in_progress") return "active";

  const stepIndex = STEP_ORDER.indexOf(step);
  const laterProgress = events.some((item) => {
    if (item.step === "error") return false;
    const index = STEP_ORDER.indexOf(item.step);
    return index > stepIndex;
  });
  if (laterProgress) return "complete";

  return "pending";
}

export function getStepMessage(step: ProgressStep, events: ProgressEvent[]): string | null {
  return events.find((item) => item.step === step)?.message ?? null;
}

export const PROGRESS_STEP_LABELS: Record<ProgressStep, string> = {
  fetching: "Fetching regions",
  scanning: "Scanning resources",
  ai: "AI enrichment",
  storing: "Storing results",
  complete: "Complete",
  error: "Error",
};

export const PROGRESS_STEPS: ProgressStep[] = STEP_ORDER;
