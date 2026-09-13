/** Shared API client — Bearer only after /auth/telegram (08_). */

export type ApiError = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  request_id?: string;
};

const TOKEN_KEY = "qp_access_token";

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  // 06_SECURITY: sessionStorage (не localStorage)
  localStorage.removeItem(TOKEN_KEY);
  if (!token) sessionStorage.removeItem(TOKEN_KEY);
  else sessionStorage.setItem(TOKEN_KEY, token);
}

function apiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE;
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "";
}

export async function api<T>(
  path: string,
  options: RequestInit & { json?: unknown; auth?: boolean; timeoutMs?: number } = {},
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");
  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const useAuth = options.auth !== false;
  const token = getToken();
  if (useAuth) {
    if (!token) {
      throw {
        http: 401,
        code: "unauthorized",
        message: "Сессия не найдена. Закройте Mini App и откройте снова через бота.",
        details: {},
      };
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  const { json, auth: _auth, timeoutMs = 15000, ...rest } = options;
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(`${apiBase()}${path}`, {
      ...rest,
      headers,
      body: json !== undefined ? JSON.stringify(json) : rest.body,
      signal: rest.signal ?? ctrl.signal,
    });
  } catch (e) {
    window.clearTimeout(timer);
    const aborted = e instanceof DOMException && e.name === "AbortError";
    throw {
      http: 0,
      code: aborted ? "timeout" : "network",
      message: aborted ? "Сервер не отвечает. Проверьте интернет и откройте снова." : "Нет связи с сервером",
      details: {},
    };
  }
  window.clearTimeout(timer);

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
  }

  if (!res.ok) {
    const err = (data as { error?: ApiError })?.error;
    let message = err?.message || res.statusText || "Ошибка запроса";
    // DRF default RU
    if (message.includes("учетные данные") || message.toLowerCase().includes("credentials")) {
      message = "Сессия истекла. Закройте Mini App и откройте снова через бота.";
    }
    throw {
      http: res.status,
      code: err?.code || "error",
      message,
      details: err?.details || {},
    };
  }
  return data as T;
}


export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}
