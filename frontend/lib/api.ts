"use client";

import { expireSession, getToken, isTokenExpired } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000/api";

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  if (token && isTokenExpired(token)) {
    expireSession();
    throw new Error("Your session has expired. Please sign in again.");
  }
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    cache: options.cache ?? "no-store",
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Request failed" }));
    if (response.status === 401 && token) {
      expireSession();
      throw new Error("Your session has expired. Please sign in again.");
    }
    throw new Error(error.message ?? error.error ?? "Request failed");
  }
  return response.json();
}

export async function apiDownload(path: string): Promise<Blob> {
  const token = getToken();
  if (token && isTokenExpired(token)) {
    expireSession();
    throw new Error("Your session has expired. Please sign in again.");
  }
  const response = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Download failed" }));
    if (response.status === 401 && token) {
      expireSession();
      throw new Error("Your session has expired. Please sign in again.");
    }
    throw new Error(error.message ?? error.error ?? "Download failed");
  }
  return response.blob();
}
