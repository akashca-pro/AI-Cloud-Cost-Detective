import { clearToken, getToken } from "./auth";

const API_BASE = "/api";

export interface ApiError {
  status: number;
  message: string;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401) {
    clearToken();
  }

  if (!response.ok) {
    const detail = await extractError(response);
    throw { status: response.status, message: detail } as ApiError;
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function extractError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.detail?.detail === "string") return data.detail.detail;
    return JSON.stringify(data);
  } catch {
    return `Request failed (${response.status})`;
  }
}

export interface AuthResponse {
  token: string;
}

export interface Credentials {
  email: string;
  password: string;
}

export const api = {
  signup: (body: Credentials) =>
    request<AuthResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: (body: Credentials) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
