"use client";

import { CheckCircle2, Lock, Save, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type RosterStudent = { id: number; registrationNumber: string; firstName: string; lastName: string; name: string };
type Entry = { studentId: number; status: "Present" | "Absent"; notes: string | null };
type RegisterPayload = {
  classId: number;
  className: string;
  date: string;
  isLocked: boolean;
  submittedAt: string | null;
  students: RosterStudent[];
  entries: Entry[];
};
type ManagedClass = { id: number; name: string; gradeLevel: number; studentCount: number };

function today() {
  return new Date().toISOString().slice(0, 10);
}

export function RegisterMarker() {
  const [classes, setClasses] = useState<ManagedClass[]>([]);
  const [managedId, setManagedId] = useState<number | null>(null);
  const [date, setDate] = useState(today());
  const [register, setRegister] = useState<RegisterPayload | null>(null);
  const [statusMap, setStatusMap] = useState<Record<number, "Present" | "Absent" | undefined>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: ManagedClass[] }>("/teacher/my-classes")
      .then((response) => {
        setClasses(response.items);
        setManagedId(response.items[0]?.id ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load your class"))
      .finally(() => setLoading(false));
  }, []);

  const managed = classes.find((item) => item.id === managedId) ?? null;

  async function loadRegister(forDate = date) {
    if (!managed) return;
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const response = await api<RegisterPayload>(`/teacher/register/${managed.id}?date=${forDate}`);
      setRegister(response);
      const initial: Record<number, "Present" | "Absent"> = {};
      response.entries.forEach((entry) => {
        initial[entry.studentId] = entry.status;
      });
      setStatusMap(initial);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load register");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (managed) loadRegister(date);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [managedId]);

  function setStatusFor(studentId: number, status: "Present" | "Absent") {
    setStatusMap((current) => ({ ...current, [studentId]: status }));
  }

  function markAll(status: "Present" | "Absent") {
    if (!register) return;
    const next: Record<number, "Present" | "Absent"> = {};
    register.students.forEach((student) => {
      next[student.id] = status;
    });
    setStatusMap(next);
  }

  async function persist(submit: boolean) {
    if (!register || !managed) return;
    if (submit && register.students.some((student) => !statusMap[student.id])) {
      setError("Mark every student Present or Absent before submitting.");
      return;
    }
    const entries = register.students
      .filter((student) => statusMap[student.id])
      .map((student) => ({ studentId: student.id, status: statusMap[student.id] }));

    submit ? setSubmitting(true) : setSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await api<{ message: string; register: RegisterPayload }>(
        `/teacher/register/${managed.id}`,
        {
          method: "POST",
          body: JSON.stringify({ date, entries, submit })
        }
      );
      setRegister(response.register);
      setMessage(response.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save register");
    } finally {
      setSaving(false);
      setSubmitting(false);
    }
  }

  if (loading && !classes.length) {
    return <Card><p className="py-8 text-center text-sm text-slate-500">Loading...</p></Card>;
  }
  if (!managed) {
    return (
      <Card>
        <h2 className="text-lg font-semibold">No class assigned</h2>
        <p className="mt-2 text-sm text-slate-500">You are not currently designated as a class teacher. Ask an administrator to assign you a class.</p>
      </Card>
    );
  }

  const locked = !!register?.isLocked;
  const counts = register
    ? register.students.reduce(
        (acc, student) => {
          const status = statusMap[student.id];
          if (status === "Present") acc.present += 1;
          else if (status === "Absent") acc.absent += 1;
          else acc.unmarked += 1;
          return acc;
        },
        { present: 0, absent: 0, unmarked: 0 }
      )
    : { present: 0, absent: 0, unmarked: 0 };

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold">{managed.name}</h2>
            <p className="text-sm text-slate-500">{managed.studentCount} active students · Grade {managed.gradeLevel}</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            {classes.length > 1 ? (
              <label className="block text-sm font-medium">
                Class
                <select
                  value={managedId ?? ""}
                  onChange={(event) => {
                    setManagedId(Number(event.target.value));
                    setRegister(null);
                    setStatusMap({});
                    setMessage("");
                    setError("");
                  }}
                  className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
                >
                  {classes.map((schoolClass) => (
                    <option key={schoolClass.id} value={schoolClass.id}>{schoolClass.name}</option>
                  ))}
                </select>
              </label>
            ) : null}
            <label className="block text-sm font-medium">
              Date
              <Input
                type="date"
                value={date}
                onChange={(event) => setDate(event.target.value)}
                max={today()}
              />
            </label>
            <Button onClick={() => loadRegister(date)} disabled={loading}>Load</Button>
          </div>
        </div>
        {locked ? (
          <p className="mt-4 flex items-center gap-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <Lock className="h-4 w-4" /> This register was submitted on {register?.submittedAt?.slice(0, 16).replace("T", " ")} and is now locked.
          </p>
        ) : null}
      </Card>

      {register ? (
        <Card className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm text-slate-500">
              <span className="font-semibold text-emerald-700">{counts.present} present</span>
              <span className="mx-2">·</span>
              <span className="font-semibold text-red-700">{counts.absent} absent</span>
              <span className="mx-2">·</span>
              <span>{counts.unmarked} unmarked</span>
            </div>
            <div className="flex gap-2">
              <button type="button" disabled={locked} onClick={() => markAll("Present")} className="rounded-md border border-emerald-200 px-3 py-1 text-sm text-emerald-700 disabled:opacity-40">Mark all present</button>
              <button type="button" disabled={locked} onClick={() => markAll("Absent")} className="rounded-md border border-red-200 px-3 py-1 text-sm text-red-700 disabled:opacity-40">Mark all absent</button>
            </div>
          </div>
          {!register.students.length ? (
            <p className="py-8 text-center text-sm text-slate-500">No active students are enrolled in this class.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-3 py-3">#</th>
                    <th className="px-3 py-3">Reg. Number</th>
                    <th className="px-3 py-3">Student</th>
                    <th className="px-3 py-3 text-center">Present</th>
                    <th className="px-3 py-3 text-center">Absent</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {register.students.map((student, index) => {
                    const current = statusMap[student.id];
                    return (
                      <tr key={student.id}>
                        <td className="px-3 py-3 text-slate-500">{index + 1}</td>
                        <td className="px-3 py-3">{student.registrationNumber}</td>
                        <td className="px-3 py-3 font-medium">{student.name}</td>
                        <td className="px-3 py-3 text-center">
                          <button
                            type="button"
                            disabled={locked}
                            onClick={() => setStatusFor(student.id, "Present")}
                            className={`inline-flex h-9 w-9 items-center justify-center rounded-full border ${
                              current === "Present" ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-300 text-slate-500 hover:border-emerald-400 hover:text-emerald-700"
                            } disabled:opacity-50`}
                            aria-label="Mark present"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </button>
                        </td>
                        <td className="px-3 py-3 text-center">
                          <button
                            type="button"
                            disabled={locked}
                            onClick={() => setStatusFor(student.id, "Absent")}
                            className={`inline-flex h-9 w-9 items-center justify-center rounded-full border ${
                              current === "Absent" ? "border-red-600 bg-red-600 text-white" : "border-slate-300 text-slate-500 hover:border-red-400 hover:text-red-700"
                            } disabled:opacity-50`}
                            aria-label="Mark absent"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          {message ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}
          <div className="flex flex-wrap justify-end gap-2">
            <Button onClick={() => persist(false)} disabled={locked || saving || submitting} className="bg-slate-700 hover:bg-slate-800">
              <Save className="h-4 w-4" /> {saving ? "Saving..." : "Save draft"}
            </Button>
            <Button
              onClick={() => {
                if (window.confirm("Submit this register? Once submitted it will be locked and cannot be edited.")) persist(true);
              }}
              disabled={locked || saving || submitting}
            >
              <Lock className="h-4 w-4" /> {submitting ? "Submitting..." : "Submit & Lock"}
            </Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
