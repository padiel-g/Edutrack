"use client";

import { CalendarDays, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type AcademicYear = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
};

export function AcademicYearsManager() {
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const response = await api<{ items: AcademicYear[] }>("/academic-years?perPage=100");
    setYears([...response.items].sort((a, b) => b.start_date.localeCompare(a.start_date)));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load academic years"));
  }, []);

  async function createYear(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      await api("/academic-years", {
        method: "POST",
        body: JSON.stringify({
          name: values.name,
          start_date: values.startDate,
          end_date: values.endDate,
          is_current: values.isCurrent === "on"
        })
      });
      form.reset();
      await load();
      setMessage("Academic year created successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create academic year");
    } finally {
      setSaving(false);
    }
  }

  async function deleteYear(year: AcademicYear) {
    if (!window.confirm(`Delete academic year ${year.name}? This cannot be undone.`)) return;
    setDeletingId(year.id);
    setError("");
    setMessage("");
    try {
      await api(`/academic-years/${year.id}`, { method: "DELETE" });
      setYears((current) => current.filter((item) => item.id !== year.id));
      setMessage("Academic year deleted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete academic year");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-teal-50 text-brand"><Plus className="h-5 w-5" /></span>
          <div><h2 className="text-lg font-semibold">Add Academic Year</h2><p className="text-sm text-slate-500">Create a new school year.</p></div>
        </div>
        <form onSubmit={createYear} className="mt-5 grid gap-4 md:grid-cols-4">
          <label className="space-y-1 text-sm font-medium">Name<Input name="name" placeholder="e.g. 2026" required /></label>
          <label className="space-y-1 text-sm font-medium">Start date<Input name="startDate" type="date" required /></label>
          <label className="space-y-1 text-sm font-medium">End date<Input name="endDate" type="date" required /></label>
          <div className="flex items-end gap-3">
            <label className="flex items-center gap-2 pb-2 text-sm"><input name="isCurrent" type="checkbox" /> Current year</label>
            <Button disabled={saving}>{saving ? "Saving..." : "Add Year"}</Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="text-lg font-semibold">Academic Years</h2>
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
          {years.map((year) => (
            <div key={year.id} className="flex items-center justify-between gap-4 border-b border-slate-100 p-4 last:border-0">
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-slate-100"><CalendarDays className="h-5 w-5 text-slate-600" /></span>
                <div>
                  <p className="font-semibold">{year.name} {year.is_current ? <span className="ml-2 rounded-full bg-teal-50 px-2 py-1 text-xs text-brand">Current</span> : null}</p>
                  <p className="text-xs text-slate-500">{year.start_date} to {year.end_date}</p>
                </div>
              </div>
              <button type="button" onClick={() => deleteYear(year)} disabled={deletingId === year.id} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50">
                <Trash2 className="h-4 w-4" />{deletingId === year.id ? "Deleting..." : "Delete"}
              </button>
            </div>
          ))}
          {!years.length ? <p className="p-8 text-center text-sm text-slate-500">No academic years found.</p> : null}
        </div>
      </Card>
      {message ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
