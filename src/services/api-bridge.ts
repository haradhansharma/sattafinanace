/**
 * FinLife API Bridge
 * ================
 * Real HTTP client for connecting to the Django Ninja backend.
 * Handles auth headers, token refresh, pagination, and error handling.
 */

// Backend API base URL — change for production
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8086/api';

// ==================== Token Storage ====================

const TOKEN_KEY = 'finlife_token';
const REFRESH_KEY = 'finlife_refresh';
const USER_KEY = 'finlife_user';

export function getStoredToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh?: string): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, access);
  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh);
  }
}

export function clearTokens(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): any | null {
  if (typeof localStorage === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function setStoredUser(user: any): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// ==================== Auth Header Helpers ====================

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ==================== Token Refresh ====================

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!res.ok) {
      clearTokens();
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    const data = await res.json();
    setTokens(data.access, data.refresh || undefined);
    return data.access;
  } catch {
    clearTokens();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return null;
  }
}

async function getValidToken(): Promise<string | null> {
  const token = getStoredToken();
  if (token) return token;

  // Try refresh
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = refreshAccessToken().finally(() => {
    isRefreshing = false;
    refreshPromise = null;
  });

  return refreshPromise;
}

// ==================== API Error ====================

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// ==================== Core Request ====================

interface RequestOptions {
  /** Skip auth header (for login/register) */
  noAuth?: boolean;
  /** Query params (appended to URL) */
  params?: Record<string, string | number | boolean | undefined | null>;
}

async function request<T>(
  method: string,
  endpoint: string,
  body?: any,
  options: RequestOptions = {}
): Promise<T> {
  const { noAuth = false, params } = options;

  // Build URL with query params
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  // Headers
  const headers = noAuth
    ? { 'Content-Type': 'application/json' }
    : await (async () => {
        const token = await getValidToken();
        const h: Record<string, string> = { 'Content-Type': 'application/json' };
        if (token) h['Authorization'] = `Bearer ${token}`;
        return h;
      })();

  // Fetch
  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Handle 401 — try refresh once
  if (res.status === 401 && !noAuth && getStoredRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      // Retry with new token
      const retryRes = await fetch(url, {
        method,
        headers: {
          ...headers,
          'Authorization': `Bearer ${newToken}`,
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
      if (!retryRes.ok) {
        const errData = await retryRes.json().catch(() => ({}));
        throw new ApiError(retryRes.status, errData.message || `Request failed with status ${retryRes.status}`, errData);
      }
      return retryRes.json();
    }
  }

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new ApiError(res.status, errData.message || `Request failed with status ${res.status}`, errData);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json();
}

// ==================== HTTP Methods ====================

export const api = {
  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>('GET', endpoint, undefined, options);
  },

  post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return request<T>('POST', endpoint, data, options);
  },

  put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return request<T>('PUT', endpoint, data, options);
  },

  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>('DELETE', endpoint, undefined, options);
  },
};

// ==================== Pagination Response ====================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/**
 * Fetch all pages from a paginated endpoint.
 * Returns concatenated items array.
 */
export async function fetchAllPages<T>(
  endpoint: string,
  options?: RequestOptions,
  maxPages: number = 20
): Promise<T[]> {
  const first = await api.get<PaginatedResponse<T>>(endpoint, {
    ...options,
    params: { ...options?.params, page: 1, per_page: 100 },
  });
  let allItems = [...first.items];
  const totalPages = Math.min(first.total_pages, maxPages);

  for (let page = 2; page <= totalPages; page++) {
    const result = await api.get<PaginatedResponse<T>>(endpoint, {
      ...options,
      params: { ...options?.params, page, per_page: 100 },
    });
    allItems = [...allItems, ...result.items];
  }

  return allItems;
}

export default api;
