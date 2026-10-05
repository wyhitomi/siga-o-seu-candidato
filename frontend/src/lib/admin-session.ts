// The admin token lives only in this browser tab (sessionStorage) and expires
// server-side after JWT_TTL_MINUTES. Public visitors never get a token.
const KEY = "siga.admin.token";

export function getToken(): string | null {
  try {
    return sessionStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  sessionStorage.setItem(KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(KEY);
}

export function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` };
}
