const ADMIN_TOKEN_KEY = "lumera_admin_token";
const ADMIN_EMAIL_KEY = "lumera_admin_email";

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ADMIN_TOKEN_KEY);
}

export function getAdminEmail(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ADMIN_EMAIL_KEY);
}

export function setAdminAuth(token: string, email: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ADMIN_TOKEN_KEY, token);
  window.localStorage.setItem(ADMIN_EMAIL_KEY, email);
  document.cookie = `${ADMIN_TOKEN_KEY}=${token}; path=/; max-age=${60 * 60 * 24}; samesite=lax`;
}

export function clearAdminAuth() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ADMIN_TOKEN_KEY);
  window.localStorage.removeItem(ADMIN_EMAIL_KEY);
  document.cookie = `${ADMIN_TOKEN_KEY}=; path=/; max-age=0; samesite=lax`;
}
