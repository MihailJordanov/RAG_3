export type StoredUser = {
  id: string;
  name?: string | null;
  email?: string | null;
  is_guest: boolean;
};

const ACCESS_TOKEN_KEY = "access_token";
const USER_KEY = "auth_user";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;

  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(USER_KEY);
}

export function clearAuth() {
  clearAccessToken();
  clearStoredUser();
}