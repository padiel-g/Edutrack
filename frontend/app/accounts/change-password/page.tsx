"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { getToken, setSession } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import type { User } from "@/types";

export default function Page() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    if (newPassword.length < 10 || !/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/\d/.test(newPassword) || !/[^A-Za-z0-9]/.test(newPassword)) {
      setError("Use at least 10 characters with uppercase, lowercase, a number, and a special character.");
      return;
    }
    setLoading(true);
    try {
      const response = await api<{ user: User; accessToken: string }>("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ currentPassword, newPassword, confirmPassword })
      });
      const token = response.accessToken || getToken();
      if (token && response.user) setSession(token, response.user);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage("Password changed successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to change password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Change Password</h1>
        <p className="text-slate-500">Replace your current password whenever you wish.</p>
      </div>
      <Card className="max-w-xl">
        <form onSubmit={submit} className="space-y-4">
          <label className="block space-y-1 text-sm font-medium">Current password<Input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required /></label>
          <label className="block space-y-1 text-sm font-medium">New password<Input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={10} required /></label>
          <label className="block space-y-1 text-sm font-medium">Confirm new password<Input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={10} required /></label>
          <p className="text-xs text-slate-500">Use at least 10 characters with uppercase, lowercase, a number, and a special character.</p>
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          {message ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}
          <Button disabled={loading}>{loading ? "Changing..." : "Change Password"}</Button>
        </form>
      </Card>
    </div>
  );
}
