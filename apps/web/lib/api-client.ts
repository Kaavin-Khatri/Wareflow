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

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getBaseUrl().replace(/\/$/, "");
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${path}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const config: RequestInit = {
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
    const response = await fetch(`${baseUrl}${path}`);
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
