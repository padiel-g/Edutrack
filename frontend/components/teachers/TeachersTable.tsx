"use client";

import Link from "next/link";
import { Eye, Plus, Search, UserCheck, UserX } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Teacher = { id: number; employeeNumber: string; name: string; email: string; department?: string; status: string };

export function TeachersTable() {
  const [items, setItems] = useState<Teacher[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  async function load() {
    try {
      const response = await api<{ items: Teacher[] }>(`/admin/teachers?search=${encodeURIComponent(search)}&status=${encodeURIComponent(status)}&perPage=50`);
      setItems(response.items);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load teachers");
    }
  }

  async function changeStatus(teacher: Teacher) {
    const nextStatus = teacher.status === "Active" ? "Suspended" : "Active";
    if (!window.confirm(`${nextStatus === "Active" ? "Reactivate" : "Suspend"} ${teacher.name}'s account?`)) return;
    setUpdatingId(teacher.id);
    setError("");
    try {
      await api(`/admin/teachers/${teacher.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update teacher access");
    } finally {
      setUpdatingId(null);
    }
  }
  useEffect(() => { load(); }, []);

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h2 className="text-lg font-semibold">Teachers</h2><p className="text-sm text-slate-500">Accounts created by administrators.</p></div>
        <Link href="/admin/teachers/create"><Button><Plus className="h-4 w-4" /> Add Teacher</Button></Link>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1"><Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" /><Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, email, or employee number" /></div>
        <select value={status} onChange={(event) => setStatus(event.target.value)} className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm">
          <option value="">All statuses</option>
          <option value="Active">Active</option>
          <option value="Suspended">Suspended</option>
          <option value="Inactive">Inactive</option>
        </select>
        <Button onClick={load}>Search</Button>
      </div>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      {!items.length ? <p className="py-8 text-center text-sm text-slate-500">No teachers have been added yet.</p> : (
        <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-3">Employee No.</th><th className="px-3 py-3">Teacher</th><th className="px-3 py-3">Department</th><th className="px-3 py-3">Status</th><th className="px-3 py-3 text-right">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{items.map((teacher) => <tr key={teacher.id}><td className="px-3 py-3">{teacher.employeeNumber}</td><td className="px-3 py-3"><p className="font-medium">{teacher.name}</p><p className="text-xs text-slate-500">{teacher.email}</p></td><td className="px-3 py-3">{teacher.department || "-"}</td><td className="px-3 py-3">{teacher.status}</td><td className="px-3 py-3"><div className="flex justify-end gap-1"><button type="button" onClick={() => changeStatus(teacher)} disabled={updatingId === teacher.id} className="rounded-md p-2 hover:bg-slate-100 disabled:opacity-50" title={teacher.status === "Active" ? "Suspend account" : "Reactivate account"}>{teacher.status === "Active" ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}</button><Link href={`/admin/teachers/${teacher.id}`} className="rounded-md p-2 hover:bg-slate-100" title="View teacher"><Eye className="h-4 w-4" /></Link></div></td></tr>)}</tbody></table></div>
      )}
    </Card>
  );
}
