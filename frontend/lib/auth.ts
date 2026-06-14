"use client";

import type { Role, User } from "@/types";

const TOKEN_KEY = "edutrack_token";
const USER_KEY = "edutrack_user";
let sessionExpiryHandled = false;

function setAuthCookies(user: User) {
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `edutrack_role=${encodeURIComponent(user.role)}; path=/; max-age=28800; SameSite=Lax${secure}`;
  document.cookie = `edutrack_must_change_password=${user.mustChangePassword ? "true" : "false"}; path=/; max-age=28800; SameSite=Lax${secure}`;
}

export function setSession(token: string, user: User) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  setAuthCookies(user);
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function isTokenExpired(token: string) {
  try {
    const payload = token.split(".")[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const normalized = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const decoded = JSON.parse(window.atob(normalized)) as { exp?: number };
    return !decoded.exp || decoded.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function restoreSessionCookies() {
  const token = getToken();
  const user = getUser();
  if (!token || !user || isTokenExpired(token)) return false;
  setAuthCookies(user);
  return true;
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  document.cookie = "edutrack_role=; path=/; max-age=0";
  document.cookie = "edutrack_must_change_password=; path=/; max-age=0";
}

export function expireSession() {
  if (typeof window === "undefined" || sessionExpiryHandled) return;
  sessionExpiryHandled = true;
  const next = `${window.location.pathname}${window.location.search}`;
  clearSession();
  window.location.replace(`/login?reason=session-expired&next=${encodeURIComponent(next)}`);
}

export function logout() {
  clearSession();
  window.location.href = "/login";
}

export const roleHome: Record<Role, string> = {
  "Super Admin": "/admin",
  Admin: "/admin",
  Teacher: "/teacher",
  Student: "/student",
  Parent: "/parent",
  "Accounts Officer": "/accounts"
};
