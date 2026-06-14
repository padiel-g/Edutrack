"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getUser, roleHome, setSession, getToken } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import type { User } from "@/types";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const user = getUser();
    if (!user) router.replace("/login");
    else if (!user.mustChangePassword) router.replace(roleHome[user.role]);
  }, [router]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    if (
      newPassword.length < 10 ||
      !/[A-Z]/.test(newPassword) ||
      !/[a-z]/.test(newPassword) ||
      !/\d/.test(newPassword) ||
      !/[^A-Za-z0-9]/.test(newPassword)
    ) {
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
      if (!token || !response.user) throw new Error("Unable to update the session.");
      setSession(token, response.user);
      router.replace(roleHome[response.user.role]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to change password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <Card className="w-full max-w-lg">
        <h1 className="text-2xl font-bold">Change Temporary Password</h1>
        <p className="mt-1 text-sm text-slate-500">Create a strong password before continuing to your portal.</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block space-y-1 text-sm font-medium">Current password<Input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required /></label>
          <label className="block space-y-1 text-sm font-medium">New password<Input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={10} required /></label>
          <label className="block space-y-1 text-sm font-medium">Confirm password<Input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={10} required /></label>
          <p className="text-xs text-slate-500">Use at least 10 characters with uppercase, lowercase, a number, and a special character.</p>
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button className="w-full" disabled={loading}>{loading ? "Changing password..." : "Change Password"}</Button>
        </form>
      </Card>
    </main>
  );
}
