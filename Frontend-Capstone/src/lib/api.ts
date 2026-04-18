import { clearSession, loadSession, saveSession } from "@/lib/session";
import type { AppSession, AuthTokensResponse } from "@/lib/types";

const API_BASE_URL = "/api/proxy";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string;
  retryOnUnauthorized?: boolean;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function buildSession(tokens: AuthTokensResponse, previous: AppSession | null): AppSession {
  return {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    expiresInSeconds: tokens.expires_in_seconds,
    createdAt: previous?.createdAt ?? Date.now(),
    user: tokens.user,
  };
}

async function refreshAccessToken(currentSession: AppSession): Promise<AppSession | null> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: currentSession.refreshToken }),
  });

  if (!response.ok) {
    clearSession();
    return null;
  }

  const payload = (await response.json()) as AuthTokensResponse;
  const nextSession = buildSession(payload, currentSession);
  saveSession(nextSession);
  return nextSession;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, token, retryOnUnauthorized = true } = options;

  const session = loadSession();
  const storedToken = token || session?.accessToken || null;
  const headers: HeadersInit = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (storedToken) {
    headers.Authorization = `Bearer ${storedToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && retryOnUnauthorized && session?.refreshToken && !token) {
    const nextSession = await refreshAccessToken(session);
    if (nextSession) {
      return apiRequest<T>(endpoint, {
        ...options,
        token: nextSession.accessToken,
        retryOnUnauthorized: false,
      });
    }
  }

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const errorMessage =
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : `Request failed with status ${response.status}`;

    throw new ApiError(errorMessage, response.status);
  }

  return data as T;
}

export function persistTokens(tokens: AuthTokensResponse): AppSession {
  const previous = loadSession();
  const session = buildSession(tokens, previous);
  saveSession(session);
  return session;
}

export async function logoutRequest(token?: string): Promise<void> {
  try {
    await apiRequest("/auth/logout", {
      method: "POST",
      token,
      retryOnUnauthorized: false,
    });
  } catch {
    return;
  }
}
