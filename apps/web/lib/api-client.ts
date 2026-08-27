/**
 * Typed API client for WareFlow web frontend.
 *
 * Communicates with the FastAPI backend.
 * Base URL configured via NEXT_PUBLIC_API_URL.
 */

export class ApiError extends Error {
  public readonly status: number;
  public readonly serverMessage: string;
  public readonly data?: unknown;

  constructor(status: number, serverMessage: string, data?: unknown) {
    super(`API Error ${status}: ${serverMessage}`);
    this.name = "ApiError";
    this.status = status;
    this.serverMessage = serverMessage;
    this.data = data;
  }
}

const getBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

const AUTH_TOKEN_STORAGE_KEY = "wareflow_auth_token";

/**
 * Firebase ID token for the signed-in user, or null when signed out.
 *
 * The API lives on a different origin than the app, so the httpOnly `session`
 * cookie never reaches it — every call has to carry a bearer token instead.
 * `authStateReady()` waits for persistence to rehydrate, otherwise calls fired
 * from a mount effect race ahead of Firebase and go out unauthenticated.
 */
export async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  if (process.env.NODE_ENV === "test") {
    return "test-bearer-token";
  }
  try {
    const { auth } = await import("./firebase-client");
    if (typeof auth?.authStateReady === "function") {
      await auth.authStateReady();
    }
    if (auth?.currentUser) {
      const token = await auth.currentUser.getIdToken();
      if (token) {
        try {
          localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
        } catch {}
        return token;
      }
    }
    // Fallback: check cached token if Firebase is rehydrating in background
    try {
      const cached = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
      if (cached) return cached;
    } catch {}
    return null;
  } catch {
    try {
      return localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    } catch {
      return null;
    }
  }
}

/**
 * Clears all cached tokens and 2FA verification keys upon user logout.
 */
export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    localStorage.removeItem(TWO_FACTOR_STORAGE_KEY);
    if (typeof document !== "undefined") {
      document.cookie = "wareflow_2fa_verified=; path=/; max-age=0; SameSite=Lax";
    }
  } catch {}
}

const TWO_FACTOR_STORAGE_KEY = "wareflow_2fa_verified";
const TWO_FACTOR_TTL_HOURS = 12;

/**
 * Checks whether the client currently holds a valid 2FA verification state.
 * Valid for up to 12 hours from completion.
 */
export function isTwoFactorVerified(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const stored = localStorage.getItem(TWO_FACTOR_STORAGE_KEY);
    if (stored) {
      if (stored === "true") return true;
      const ts = parseInt(stored, 10);
      if (!isNaN(ts)) {
        const elapsedHours = (Date.now() - ts) / (1000 * 60 * 60);
        if (elapsedHours < TWO_FACTOR_TTL_HOURS) {
          return true;
        }
        localStorage.removeItem(TWO_FACTOR_STORAGE_KEY);
      }
    }
    // Fallback: check cookie
    if (typeof document !== "undefined" && document.cookie.includes("wareflow_2fa_verified=true")) {
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

/**
 * Updates the 2FA verification state in client storage and browser cookies.
 */
export function setTwoFactorVerified(verified: boolean): void {
  if (typeof window === "undefined") return;
  try {
    if (verified) {
      localStorage.setItem(TWO_FACTOR_STORAGE_KEY, String(Date.now()));
      if (typeof document !== "undefined") {
        document.cookie = "wareflow_2fa_verified=true; path=/; max-age=43200; SameSite=Lax";
      }
    } else {
      localStorage.removeItem(TWO_FACTOR_STORAGE_KEY);
      if (typeof document !== "undefined") {
        document.cookie = "wareflow_2fa_verified=; path=/; max-age=0; SameSite=Lax";
      }
    }
  } catch {
    // Ignore storage quota or access errors in restricted browser contexts
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getBaseUrl().replace(/\/$/, "");
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${path}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Authorization")) {
    const token = await getAuthToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  // Inject 2FA verification header if user verified TOTP
  if (!headers.has("X-2FA-Verified") && isTwoFactorVerified()) {
    headers.set("X-2FA-Verified", "true");
  }

  const config: RequestInit = {
    credentials: "include",
    ...options,
    headers,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let serverMessage = response.statusText;
    let data: unknown;

    try {
      data = await response.json();
      if (data && typeof data === "object" && "detail" in data) {
        serverMessage = String((data as { detail: unknown }).detail);
      } else if (data && typeof data === "object" && "message" in data) {
        serverMessage = String((data as { message: unknown }).message);
      }
    } catch {
      // Body wasn't JSON, fallback to statusText
    }

    // If 2FA is required by the backend, notify UI listeners ONLY if not already verified
    if (
      response.status === 403 &&
      typeof window !== "undefined" &&
      serverMessage.toLowerCase().includes("two-factor")
    ) {
      if (!isTwoFactorVerified()) {
        window.dispatchEvent(
          new CustomEvent("wareflow:2fa-required", {
            detail: { endpoint, serverMessage },
          })
        );
      }
    }

    throw new ApiError(response.status, serverMessage, data);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, { ...options, method: "GET" });
  },

  post<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  put<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  patch<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, { ...options, method: "DELETE" });
  },

  upload<T>(endpoint: string, formData: FormData, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      ...options,
      method: "POST",
      body: formData,
    });
  },

  async downloadBlob(endpoint: string, filename: string): Promise<void> {
    const baseUrl = getBaseUrl().replace(/\/$/, "");
    const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const token = await getAuthToken();
    const requestUrl = `${baseUrl}${path}`;
    const response = token
      ? await fetch(requestUrl, { headers: { Authorization: `Bearer ${token}` } })
      : await fetch(requestUrl);
    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
