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

type Term = {
  id: number;
  name: string;
  academic_year_id: number;
  start_date: string;
  end_date: string;
  is_current: boolean;
};

export function AcademicYearsManager() {
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [terms, setTerms] = useState<Term[]>([]);
  const [saving, setSaving] = useState(false);
  const [savingTerm, setSavingTerm] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deletingTermId, setDeletingTermId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const [yearResponse, termResponse] = await Promise.all([
      api<{ items: AcademicYear[] }>("/academic-years?perPage=100"),
      api<{ items: Term[] }>("/terms?perPage=100"),
    ]);
    setYears([...yearResponse.items].sort((a, b) => b.start_date.localeCompare(a.start_date)));
    setTerms([...termResponse.items].sort((a, b) => b.start_date.localeCompare(a.start_date)));
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

  async function createTerm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingTerm(true);
    setError("");
    setMessage("");
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      await api("/terms", {
        method: "POST",
        body: JSON.stringify({
          name: values.name,
          academic_year_id: Number(values.academicYearId),
          start_date: values.startDate,
          end_date: values.endDate,
          is_current: values.isCurrent === "on"
        })
      });
      form.reset();
      await load();
      setMessage("Term created successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create term");
    } finally {
      setSavingTerm(false);
    }
  }

  async function deleteTerm(term: Term) {
    if (!window.confirm(`Delete term ${term.name}? This cannot be undone.`)) return;
    setDeletingTermId(term.id);
    setError("");
    setMessage("");
    try {
      await api(`/terms/${term.id}`, { method: "DELETE" });
      setTerms((current) => current.filter((item) => item.id !== term.id));
      setMessage("Term deleted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete term");
    } finally {
      setDeletingTermId(null);
    }
  }

  function termsForYear(yearId: number) {
    return terms.filter((term) => term.academic_year_id === yearId);
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
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-teal-50 text-brand"><Plus className="h-5 w-5" /></span>
          <div><h2 className="text-lg font-semibold">Add Term</h2><p className="text-sm text-slate-500">Create a term inside an academic year.</p></div>
        </div>
        <form onSubmit={createTerm} className="mt-5 grid gap-4 md:grid-cols-5">
          <label className="space-y-1 text-sm font-medium">Academic year
            <select name="academicYearId" required className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm">
              <option value="">Select year</option>
              {years.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
            </select>
          </label>
          <label className="space-y-1 text-sm font-medium">Term name<Input name="name" placeholder="e.g. Term 1" required /></label>
          <label className="space-y-1 text-sm font-medium">Start date<Input name="startDate" type="date" required /></label>
          <label className="space-y-1 text-sm font-medium">End date<Input name="endDate" type="date" required /></label>
          <div className="flex items-end gap-3">
            <label className="flex items-center gap-2 pb-2 text-sm"><input name="isCurrent" type="checkbox" /> Current term</label>
            <Button disabled={savingTerm || !years.length}>{savingTerm ? "Saving..." : "Add Term"}</Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="text-lg font-semibold">Academic Years and Terms</h2>
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
          {years.map((year) => (
            <div key={year.id} className="border-b border-slate-100 p-4 last:border-0">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-lg bg-slate-100"><CalendarDays className="h-5 w-5 text-slate-600" /></span>
                  <div>
                    <p className="font-semibold">{year.name} {year.is_current ? <span className="ml-2 rounded-full bg-teal-50 px-2 py-1 text-xs text-brand">Current year</span> : null}</p>
                    <p className="text-xs text-slate-500">{year.start_date} to {year.end_date}</p>
                  </div>
                </div>
                <button type="button" onClick={() => deleteYear(year)} disabled={deletingId === year.id} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50">
                  <Trash2 className="h-4 w-4" />{deletingId === year.id ? "Deleting..." : "Delete year"}
                </button>
              </div>
              <div className="mt-4 grid gap-2 pl-0 md:pl-14">
                {termsForYear(year.id).map((term) => (
                  <div key={term.id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2">
                    <div>
                      <p className="text-sm font-semibold">{term.name} {term.is_current ? <span className="ml-2 rounded-full bg-white px-2 py-1 text-xs text-brand">Current term</span> : null}</p>
                      <p className="text-xs text-slate-500">{term.start_date} to {term.end_date}</p>
                    </div>
                    <button type="button" onClick={() => deleteTerm(term)} disabled={deletingTermId === term.id} className="inline-flex items-center gap-2 rounded-md px-2 py-1 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50">
                      <Trash2 className="h-3.5 w-3.5" />{deletingTermId === term.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                ))}
                {!termsForYear(year.id).length ? <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-500">No terms have been added for this academic year.</p> : null}
              </div>
            </div>
          ))}
          {!years.length ? <p className="p-8 text-center text-sm text-slate-500">No academic years found.</p> : null}
          {years.length && terms.some((term) => !term.academic_year_id) ? (
            <div className="border-t border-slate-100 p-4">
              <h3 className="text-sm font-semibold">Unassigned terms</h3>
              <div className="mt-3 grid gap-2">
                {terms.filter((term) => !term.academic_year_id).map((term) => (
                  <div key={term.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
                    <div>
                      <p className="text-sm font-semibold">{term.name}</p>
                      <p className="text-xs text-slate-500">{term.start_date} to {term.end_date}</p>
                    </div>
                    <button type="button" onClick={() => deleteTerm(term)} disabled={deletingTermId === term.id} className="inline-flex items-center gap-2 rounded-md px-2 py-1 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50">
                      <Trash2 className="h-3.5 w-3.5" />{deletingTermId === term.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </Card>
      {message ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
