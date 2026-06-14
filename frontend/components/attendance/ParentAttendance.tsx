"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type AttendanceRow = { date: string; status: string; notes: string | null; className: string | null };
type Response = {
  student: { id: number; registrationNumber: string; name: string; className: string | null };
  summary: { total: number; present: number; absent: number; presentRate: number };
  items: AttendanceRow[];
};

export function ParentAttendance() {
  const [data, setData] = useState<Response | null>(null);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (from) params.set("from", from);
      if (to) params.set("to", to);
      const query = params.toString();
      const response = await api<Response>(`/parent/attendance${query ? `?${query}` : ""}`);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load attendance");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-5">
      <Card>
        <h2 className="text-lg font-semibold">Filter</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_1fr_140px]">
          <label className="block space-y-1 text-sm font-medium">From<Input type="date" value={from} onChange={(event) => setFrom(event.target.value)} /></label>
          <label className="block space-y-1 text-sm font-medium">To<Input type="date" value={to} onChange={(event) => setTo(event.target.value)} /></label>
          <div className="flex items-end"><Button onClick={load} disabled={loading} className="w-full">Apply</Button></div>
        </div>
        {error ? <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      </Card>

      {data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-4">
            <Card>
              <p className="text-sm text-slate-500">Student</p>
              <p className="mt-1 text-lg font-semibold">{data.student.name}</p>
              <p className="text-xs text-slate-500">{data.student.registrationNumber}</p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Days recorded</p>
              <p className="mt-1 text-3xl font-bold">{data.summary.total}</p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Present</p>
              <p className="mt-1 text-3xl font-bold text-emerald-700">{data.summary.present}</p>
              <p className="mt-1 text-xs text-emerald-700">{data.summary.presentRate}%</p>
            </Card>
            <Card>
              <p className="text-sm text-slate-500">Absent</p>
              <p className="mt-1 text-3xl font-bold text-red-700">{data.summary.absent}</p>
            </Card>
          </div>

          <Card>
            <h2 className="text-lg font-semibold">Attendance history</h2>
            {!data.items.length ? (
              <p className="py-8 text-center text-sm text-slate-500">No registers have been submitted for {data.student.name} in this range.</p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[480px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-3 py-3">Date</th>
                      <th className="px-3 py-3">Class</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-3 py-3">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.items.map((row) => (
                      <tr key={`${row.date}-${row.className ?? ""}`}>
                        <td className="px-3 py-3 font-medium">{row.date}</td>
                        <td className="px-3 py-3">{row.className ?? "-"}</td>
                        <td className="px-3 py-3">
                          {row.status === "Present" ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" />Present</span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700"><XCircle className="h-3.5 w-3.5" />Absent</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-500">{row.notes ?? "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      ) : (
        <Card><p className="py-8 text-center text-sm text-slate-500">{loading ? "Loading..." : "No attendance data."}</p></Card>
      )}
    </div>
  );
}
