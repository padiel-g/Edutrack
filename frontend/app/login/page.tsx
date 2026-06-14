"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GraduationCap, ShieldCheck, UsersRound, WalletCards } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import { roleHome, setSession } from "@/lib/auth";
import type { Role, User } from "@/types";

const loginRoles: { label: Role; icon: typeof ShieldCheck }[] = [
  { label: "Admin", icon: ShieldCheck },
  { label: "Teacher", icon: GraduationCap },
  { label: "Parent", icon: UsersRound },
  { label: "Accounts Officer", icon: WalletCards }
];

export default function LoginPage() {
  const router = useRouter();
  const [selectedRole, setSelectedRole] = useState<Role>("Admin");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const reason = new URLSearchParams(window.location.search).get("reason");
    if (reason === "session-expired") {
      setNotice("Your session expired. Sign in again to continue. Your saved records are unchanged.");
    }
  }, []);

  async function signIn(accountIdentifier = identifier, accountPassword = password) {
    setLoading(true);
    setError("");
    try {
      const data = await api<{ accessToken: string; user: User; redirectPath?: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: selectedRole === "Parent" ? undefined : accountIdentifier,
          registrationNumber: selectedRole === "Parent" ? accountIdentifier : undefined,
          password: accountPassword,
          role: selectedRole
        })
      });
      if (data.user.role !== selectedRole) {
        throw new Error(`This account is registered as ${data.user.role}, not ${selectedRole}.`);
      }
      setSession(data.accessToken, data.user);
      router.push(data.redirectPath ?? roleHome[data.user.role]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await signIn();
  }

  return (
    <main
      className="grid min-h-screen place-items-center bg-slate-100 bg-cover bg-center bg-no-repeat px-4"
      style={{ backgroundImage: "linear-gradient(rgba(15, 23, 42, 0.28), rgba(15, 23, 42, 0.28)), url('/image.png')" }}
    >
      <Card className="w-full max-w-xl bg-white/95 shadow-2xl backdrop-blur">
        <h1 className="text-2xl font-bold">Sign in to EduTrack</h1>
        <p className="mt-1 text-sm text-slate-500">Select your portal and use your registered school account credentials.</p>
        {notice ? <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{notice}</p> : null}
        <form onSubmit={submit} className="mt-6 space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {loginRoles.map((role) => {
              const Icon = role.icon;
              const isSelected = selectedRole === role.label;
              return (
                <button
                  key={role.label}
                  type="button"
                  onClick={() => setSelectedRole(role.label)}
                  className={`flex h-20 flex-col items-center justify-center gap-2 rounded-md border px-2 text-sm font-semibold transition ${
                    isSelected
                      ? "border-brand bg-teal-50 text-brand"
                      : "border-slate-200 bg-white text-slate-700 hover:border-brand hover:bg-slate-50"
                  }`}
                  aria-pressed={isSelected}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                  <span>{role.label === "Accounts Officer" ? "Accounts" : role.label}</span>
                </button>
              );
            })}
          </div>
          <label className="block space-y-1 text-sm font-medium">
            {selectedRole === "Parent" ? "Student registration number" : "Email"}
            <Input
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              type={selectedRole === "Parent" ? "text" : "email"}
              autoComplete="username"
              required
            />
          </label>
          <label className="block space-y-1 text-sm font-medium">Password<Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required /></label>
          {selectedRole === "Teacher" ? <Link href="/forgot-password" className="block text-right text-sm font-semibold text-brand">Forgot password?</Link> : null}
          {selectedRole === "Parent" ? <p className="text-xs text-slate-500">Use the temporary password issued during student registration. You will change it after signing in.</p> : null}
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button className="w-full" disabled={loading}>{loading ? "Signing in..." : "Login"}</Button>
        </form>
      </Card>
    </main>
  );
}
