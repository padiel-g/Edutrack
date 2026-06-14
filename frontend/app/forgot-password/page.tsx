"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<"request" | "verify" | "reset" | "done">("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function requestCode(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api<{ message: string }>("/auth/forgot-password/request", {
        method: "POST",
        body: JSON.stringify({ email })
      });
      setMessage(response.message);
      setStep("verify");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to request a verification code");
    } finally {
      setLoading(false);
    }
  }

  async function verifyCode(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api<{ resetToken: string }>("/auth/forgot-password/verify", {
        method: "POST",
        body: JSON.stringify({ email, code })
      });
      setResetToken(response.resetToken);
      setMessage("");
      setStep("reset");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to verify the code");
    } finally {
      setLoading(false);
    }
  }

  async function resetPassword(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    setLoading(true);
    try {
      const response = await api<{ message: string }>("/auth/forgot-password/reset", {
        method: "POST",
        body: JSON.stringify({ email, resetToken, newPassword, confirmPassword })
      });
      setMessage(response.message);
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reset password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-bold">Reset Teacher Password</h1>
        <p className="mt-1 text-sm text-slate-500">A verification code will be sent to your registered teacher email address.</p>

        {step === "request" ? (
          <form onSubmit={requestCode} className="mt-6 space-y-4">
            <label className="block space-y-1 text-sm font-medium">Teacher email<Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label>
            <Button className="w-full" disabled={loading}>{loading ? "Sending..." : "Send Email Code"}</Button>
          </form>
        ) : null}

        {step === "verify" ? (
          <form onSubmit={verifyCode} className="mt-6 space-y-4">
            {message ? <p className="rounded-md bg-teal-50 px-3 py-2 text-sm text-brand">{message}</p> : null}
            <label className="block space-y-1 text-sm font-medium">Six-digit verification code<Input value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} inputMode="numeric" pattern="\d{6}" autoComplete="one-time-code" required /></label>
            <Button className="w-full" disabled={loading || code.length !== 6}>{loading ? "Verifying..." : "Verify Code"}</Button>
            <button type="button" onClick={() => setStep("request")} className="w-full text-sm font-semibold text-brand">Request another code</button>
          </form>
        ) : null}

        {step === "reset" ? (
          <form onSubmit={resetPassword} className="mt-6 space-y-4">
            <label className="block space-y-1 text-sm font-medium">New password<Input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={10} autoComplete="new-password" required /></label>
            <label className="block space-y-1 text-sm font-medium">Confirm password<Input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={10} autoComplete="new-password" required /></label>
            <p className="text-xs text-slate-500">Use at least 10 characters with uppercase, lowercase, a number, and a special character.</p>
            <Button className="w-full" disabled={loading}>{loading ? "Resetting..." : "Reset Password"}</Button>
          </form>
        ) : null}

        {step === "done" ? (
          <div className="mt-6 space-y-4">
            <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p>
            <Link href="/login" className="flex h-10 items-center justify-center rounded-md bg-brand px-4 text-sm font-semibold text-white">Return to Login</Link>
          </div>
        ) : null}

        {error ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        {step !== "done" ? <Link href="/login" className="mt-4 block text-center text-sm font-semibold text-brand">Back to login</Link> : null}
      </Card>
    </main>
  );
}
