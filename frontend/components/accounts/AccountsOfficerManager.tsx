"use client";

import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import type { User } from "@/types";

export function AccountsOfficerManager() {
  const [items, setItems] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const response = await api<{ items: User[] }>("/users?role=Accounts%20Officer&perPage=100");
    setItems(response.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load accounts"));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      const response = await api<{ user: User; defaultPassword: string }>("/auth/accounts", {
        method: "POST",
        body: JSON.stringify({
          firstName: data.get("firstName"),
          lastName: data.get("lastName"),
          email: data.get("email"),
          phone: data.get("phone")
        })
      });
      setMessage(`Account created. Temporary password: ${response.defaultPassword}`);
      form.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create account");
    } finally {
      setLoading(false);
    }
  }

  async function deleteOfficer(user: User) {
    if (!window.confirm(`Delete ${user.name}'s Accounts Officer account? This only works when the account has no finance records.`)) return;
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await api(`/auth/accounts/${user.id}`, { method: "DELETE" });
      setMessage("Accounts Officer account deleted.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete Accounts Officer account");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <Card>
        <h2 className="text-lg font-semibold">Create Accounts Officer</h2>
        <p className="mt-1 text-sm text-slate-500">A unique temporary password is generated once. The officer must change it after signing in.</p>
        <form onSubmit={submit} className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm font-medium">First name<Input name="firstName" required /></label>
          <label className="space-y-1 text-sm font-medium">Last name<Input name="lastName" required /></label>
          <label className="space-y-1 text-sm font-medium">Email<Input name="email" type="email" required /></label>
          <label className="space-y-1 text-sm font-medium">Phone<Input name="phone" /></label>
          <div className="md:col-span-2"><Button disabled={loading}>{loading ? "Creating..." : "Create Account"}</Button></div>
        </form>
        {error ? <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        {message ? <p className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}
      </Card>

      <Card>
        <h2 className="text-lg font-semibold">Accounts Officers</h2>
        {!items.length ? <p className="py-8 text-center text-sm text-slate-500">No Accounts Officer accounts found.</p> : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-3">Name</th><th className="px-3 py-3">Email</th><th className="px-3 py-3">Status</th><th className="px-3 py-3">Last login</th><th className="px-3 py-3 text-right">Actions</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((user) => <tr key={user.id}><td className="px-3 py-3 font-medium">{user.name}</td><td className="px-3 py-3">{user.email}</td><td className="px-3 py-3">{user.status}</td><td className="px-3 py-3 text-slate-500">{user.lastLoginAt?.slice(0, 16).replace("T", " ") ?? "Never"}</td><td className="px-3 py-3 text-right"><button type="button" onClick={() => deleteOfficer(user)} disabled={loading} className="rounded-md p-2 text-coral hover:bg-red-50 disabled:opacity-50" title="Delete Accounts Officer account"><Trash2 className="h-4 w-4" /></button></td></tr>)}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
