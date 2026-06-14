"use client";

import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Subject = { id: number; code: string; name: string };
type ExamEntry = {
  id: number;
  examDate: string;
  classType: string;
  subject: Subject;
  startTime: string;
  endTime: string;
  venue?: string;
  paper?: string;
  notes?: string;
};

export function ExamTimetableManager({ canManage = false }: { canManage?: boolean }) {
  const [entries, setEntries] = useState<ExamEntry[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const timetable = await api<{ items: ExamEntry[] }>("/exam-timetables");
    setEntries(timetable.items);
    if (canManage) {
      const subjectResponse = await api<{ items: Subject[] }>("/subjects?perPage=100");
      setSubjects(subjectResponse.items);
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load exam timetable"));
  }, [canManage]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      await api("/exam-timetables", {
        method: "POST",
        body: JSON.stringify({ ...values, subjectId: Number(values.subjectId) })
      });
      form.reset();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create exam timetable");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this exam timetable entry?")) return;
    await api(`/exam-timetables/${id}`, { method: "DELETE" });
    await load();
  }

  return (
    <div className={canManage ? "grid gap-5 xl:grid-cols-[1fr_420px]" : ""}>
      <Card>
        <h2 className="text-lg font-semibold">Exam Timetable</h2>
        {!entries.length ? <p className="py-8 text-center text-sm text-slate-500">No exam timetable has been created yet.</p> : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-3">Date</th>
                  <th className="px-3 py-3">Class Type</th>
                  <th className="px-3 py-3">Subject</th>
                  <th className="px-3 py-3">Paper</th>
                  <th className="px-3 py-3">Time</th>
                  <th className="px-3 py-3">Venue</th>
                  {canManage ? <th className="px-3 py-3 text-right">Actions</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-3 py-3">{new Date(`${entry.examDate}T00:00:00`).toLocaleDateString()}</td>
                    <td className="px-3 py-3">{entry.classType}</td>
                    <td className="px-3 py-3 font-medium">{entry.subject?.name ?? "-"}</td>
                    <td className="px-3 py-3">{entry.paper || "-"}</td>
                    <td className="px-3 py-3">{entry.startTime} - {entry.endTime}</td>
                    <td className="px-3 py-3">{entry.venue || "-"}</td>
                    {canManage ? (
                      <td className="px-3 py-3 text-right">
                        <button onClick={() => remove(entry.id)} className="rounded-md p-2 text-coral" aria-label="Delete exam">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {canManage ? (
        <Card>
          <h2 className="text-lg font-semibold">Create Exam Entry</h2>
          <form onSubmit={submit} className="mt-4 space-y-4">
            <label className="block space-y-1 text-sm font-medium">Exam date <span className="text-coral">*</span><Input name="examDate" type="date" required /></label>
            <label className="block space-y-1 text-sm font-medium">Class type <span className="text-coral">*</span><Input name="classType" required /></label>
            <label className="block space-y-1 text-sm font-medium">
              Subject <span className="text-coral">*</span>
              <select name="subjectId" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                <option value="">Select subject</option>
                {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.code} - {subject.name}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-sm font-medium">Paper<Input name="paper" /></label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block space-y-1 text-sm font-medium">Start time <span className="text-coral">*</span><Input name="startTime" type="time" required /></label>
              <label className="block space-y-1 text-sm font-medium">End time <span className="text-coral">*</span><Input name="endTime" type="time" required /></label>
            </div>
            <label className="block space-y-1 text-sm font-medium">Venue<Input name="venue" /></label>
            <label className="block space-y-1 text-sm font-medium">Notes<textarea name="notes" className="min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" /></label>
            {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
            <Button className="w-full" disabled={loading}>{loading ? "Saving..." : "Add Exam"}</Button>
          </form>
        </Card>
      ) : error ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
