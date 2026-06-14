"use client";

import { BookOpen, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

type Subject = { id: number; code: string; name: string };
type SchoolClass = { id: number; name: string };

export function MySubjectsManager() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api<{ availableSubjects: Subject[]; assignedSubjects: Subject[]; assignedClasses: SchoolClass[] }>("/teacher/subjects")
      .then((response) => {
        setSubjects(response.availableSubjects);
        setSelected(response.assignedSubjects.map((subject) => subject.id));
        setClasses(response.assignedClasses);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load subjects"))
      .finally(() => setLoading(false));
  }, []);

  function toggle(subjectId: number) {
    setSelected((current) =>
      current.includes(subjectId)
        ? current.filter((id) => id !== subjectId)
        : [...current, subjectId]
    );
  }

  async function save() {
    if (!window.confirm("Save these changes to your teaching subjects? The administrator will be able to review this change.")) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await api("/teacher/subjects", {
        method: "PUT",
        body: JSON.stringify({ subjectIds: selected })
      });
      setMessage("Teaching subjects updated. The change has been recorded for the administrator.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update subjects");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">My Subjects</h1>
        <p className="text-slate-500">Review and update the subjects you teach.</p>
      </div>
      <Card>
        <div className="border-b border-slate-200 pb-4">
          <h2 className="font-semibold">Assigned classes</h2>
          <p className="mt-1 text-sm text-slate-500">
            {classes.length ? classes.map((item) => item.name).join(", ") : "No classes have been assigned yet."}
          </p>
        </div>
        {loading ? <p className="py-10 text-center text-sm text-slate-500">Loading subjects...</p> : (
          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {subjects.map((subject) => (
              <label key={subject.id} className="flex cursor-pointer items-center gap-3 rounded-md border border-slate-200 p-3 hover:bg-slate-50">
                <input type="checkbox" checked={selected.includes(subject.id)} onChange={() => toggle(subject.id)} className="h-4 w-4 accent-teal-700" />
                <BookOpen className="h-4 w-4 text-slate-400" />
                <span className="min-w-0">
                  <span className="block font-medium">{subject.name}</span>
                  <span className="block text-xs text-slate-500">{subject.code}</span>
                </span>
              </label>
            ))}
          </div>
        )}
        {!loading && !subjects.length ? <p className="py-10 text-center text-sm text-slate-500">No subjects have been created by the administrator.</p> : null}
        {error ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        {message ? <p className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p> : null}
        <div className="mt-5 flex justify-end">
          <Button onClick={save} disabled={loading || saving}>
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : "Save Subject Changes"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
