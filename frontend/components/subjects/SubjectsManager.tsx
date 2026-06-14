"use client";

import { BookOpen, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Subject = {
  id: number;
  code: string;
  name: string;
  stream?: string | null;
};

export function SubjectsManager() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const filteredSubjects = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return subjects;
    return subjects.filter((subject) =>
      [subject.code, subject.name, subject.stream].some((value) =>
        value?.toLowerCase().includes(query)
      )
    );
  }, [search, subjects]);

  async function loadSubjects() {
    const response = await api<{ items: Subject[] }>("/subjects?perPage=100");
    setSubjects(
      [...response.items].sort((a, b) => a.name.localeCompare(b.name))
    );
  }

  useEffect(() => {
    loadSubjects().catch((err) =>
      setError(err instanceof Error ? err.message : "Unable to load subjects")
    );
  }, []);

  async function addSubject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    const form = event.currentTarget;
    const data = new FormData(form);

    try {
      await api("/subjects", {
        method: "POST",
        body: JSON.stringify({
          name: String(data.get("name") ?? "").trim(),
          code: String(data.get("code") ?? "").trim().toUpperCase(),
          stream: String(data.get("stream") ?? "").trim() || null
        })
      });
      form.reset();
      await loadSubjects();
      setMessage("Subject added successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to add subject");
    } finally {
      setSaving(false);
    }
  }

  async function deleteSubject(subject: Subject) {
    if (!window.confirm(`Delete ${subject.name} (${subject.code})?`)) return;
    setDeletingId(subject.id);
    setError("");
    setMessage("");

    try {
      await api(`/subjects/${subject.id}`, { method: "DELETE" });
      setSubjects((current) => current.filter((item) => item.id !== subject.id));
      setMessage("Subject deleted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete subject");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-teal-50 text-brand">
            <Plus className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-lg font-semibold">Add Subject</h2>
            <p className="text-sm text-slate-500">Create a subject for classes, teachers, and students.</p>
          </div>
        </div>

        <form onSubmit={addSubject} className="mt-5 grid gap-4 md:grid-cols-[1fr_180px_1fr_auto]">
          <label className="space-y-1 text-sm font-medium">
            Subject name
            <Input name="name" placeholder="e.g. Mathematics" required />
          </label>
          <label className="space-y-1 text-sm font-medium">
            Code
            <Input name="code" placeholder="e.g. MATH" required />
          </label>
          <label className="space-y-1 text-sm font-medium">
            Stream
            <Input name="stream" placeholder="Optional" />
          </label>
          <div className="flex items-end">
            <Button className="w-full md:w-auto" disabled={saving}>
              {saving ? "Adding..." : "Add Subject"}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Subjects</h2>
            <p className="text-sm text-slate-500">{subjects.length} subjects available</p>
          </div>
          <label className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <Input
              className="w-64 pl-9"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search subjects"
            />
          </label>
        </div>

        <div className="mt-5 overflow-hidden rounded-xl border border-slate-200">
          {filteredSubjects.map((subject) => (
            <div key={subject.id} className="flex items-center justify-between gap-4 border-b border-slate-100 p-4 last:border-0">
              <div className="flex min-w-0 items-center gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-600">
                  <BookOpen className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="truncate font-semibold">{subject.name}</p>
                  <p className="text-xs text-slate-500">
                    {subject.code}{subject.stream ? ` · ${subject.stream}` : ""}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => deleteSubject(subject)}
                disabled={deletingId === subject.id}
                className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                <Trash2 className="h-4 w-4" />
                {deletingId === subject.id ? "Deleting..." : "Delete"}
              </button>
            </div>
          ))}
          {!filteredSubjects.length ? (
            <p className="p-8 text-center text-sm text-slate-500">No subjects found.</p>
          ) : null}
        </div>
      </Card>

      {message ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
