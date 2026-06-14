"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type SchoolClass = {
  id: number;
  name: string;
  classTeacherId?: number | null;
  classTeacher?: { id: number; name: string } | null;
};
type RegisterSummary = {
  id: number;
  classId: number;
  className: string;
  teacherId: number;
  teacherName: string;
  date: string;
  submittedAt: string | null;
  isLocked: boolean;
};
type RegisterStudent = { id: number; registrationNumber: string; name: string };
type RegisterEntry = { id: number; studentId: number; status: string; notes: string | null };
type RegisterDetail = RegisterSummary & { students: RegisterStudent[]; entries: RegisterEntry[] };

export function AdminRegisters() {
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [teacherClass, setTeacherClass] = useState<string>("");
  const [date, setDate] = useState<string>("");
  const [detail, setDetail] = useState<RegisterDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadClasses() {
    const response = await api<{ items: SchoolClass[] }>("/classes?perPage=200");
    setClasses(response.items);
  }

  const classTeacherAssignments = classes
    .filter((schoolClass) => schoolClass.classTeacher)
    .sort((a, b) => {
      const teacherOrder = a.classTeacher!.name.localeCompare(b.classTeacher!.name);
      return teacherOrder || a.name.localeCompare(b.name);
    });

  async function loadRegister() {
    if (!teacherClass || !date) {
      setError("Select a class teacher and date.");
      setDetail(null);
      return;
    }
    const [teacherId, classId] = teacherClass.split(":");
    setLoading(true);
    setError("");
    setDetail(null);
    try {
      const params = new URLSearchParams({ teacherId, classId, date, perPage: "10" });
      const response = await api<{ items: RegisterSummary[] }>(`/admin/registers?${params}`);
      const item = response.items[0];
      if (!item) {
        setError("No submitted register was found for this class teacher on the selected date.");
        return;
      }
      const registerResponse = await api<{ register: RegisterDetail }>(`/admin/registers/${item.classId}/${item.date}`);
      setDetail(registerResponse.register);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load register");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadClasses().catch((err) => setError(err instanceof Error ? err.message : "Unable to load classes"));
  }, []);

  const entryMap = new Map((detail?.entries ?? []).map((entry) => [entry.studentId, entry]));

  return (
    <div className="space-y-5">
      <Card>
        <h2 className="text-lg font-semibold">View class register</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_180px_140px]">
          <label className="block space-y-1 text-sm font-medium">
            Class Teacher
            <select value={teacherClass} onChange={(event) => setTeacherClass(event.target.value)} className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              <option value="">Select class teacher</option>
              {classTeacherAssignments.map((schoolClass) => (
                <option key={schoolClass.id} value={`${schoolClass.classTeacher!.id}:${schoolClass.id}`}>
                  {schoolClass.classTeacher!.name} - {schoolClass.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1 text-sm font-medium">
            Date
            <Input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
          </label>
          <div className="flex items-end"><Button onClick={loadRegister} disabled={loading || !teacherClass || !date} className="w-full">{loading ? "Loading..." : "View Register"}</Button></div>
        </div>
        {error ? <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      </Card>

      {detail ? (
        <Card>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold">{detail.className} · {detail.date}</h2>
              <p className="text-sm text-slate-500">Submitted by {detail.teacherName} at {detail.submittedAt?.slice(0, 16).replace("T", " ")}</p>
            </div>
            <button onClick={() => setDetail(null)} className="rounded-md border border-slate-200 px-3 py-1 text-sm text-slate-600 hover:bg-slate-50">Close</button>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-3">#</th>
                  <th className="px-3 py-3">Reg. Number</th>
                  <th className="px-3 py-3">Student</th>
                  <th className="px-3 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {detail.students.map((student, index) => {
                  const entry = entryMap.get(student.id);
                  const status = entry?.status ?? "Not marked";
                  return (
                    <tr key={student.id}>
                      <td className="px-3 py-3 text-slate-500">{index + 1}</td>
                      <td className="px-3 py-3">{student.registrationNumber}</td>
                      <td className="px-3 py-3 font-medium">{student.name}</td>
                      <td className="px-3 py-3">
                        {status === "Present" ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" />Present</span>
                        ) : status === "Absent" ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700"><XCircle className="h-3.5 w-3.5" />Absent</span>
                        ) : (
                          <span className="text-xs text-slate-500">{status}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
