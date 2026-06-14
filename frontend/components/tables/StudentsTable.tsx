"use client";

import Link from "next/link";
import { Edit, Eye, Search, Trash2, UserPlus } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import type { Student } from "@/types/student";

export function StudentsTable() {
  const [students, setStudents] = useState<Student[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams({ search, status });
      const response = await api<{ items: Student[] }>(`/admin/students?${query}`);
      setStudents(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load students");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function deactivate(id: number) {
    if (!confirm("Deactivate this student?")) return;
    await api(`/admin/students/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <Card className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Registered Students</h2>
          <p className="text-sm text-slate-500">Search, filter, profile, edit, assign, link guardians, and deactivate students.</p>
        </div>
        <Link href="/admin/students/register"><Button><UserPlus className="h-4 w-4" /> Register student</Button></Link>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_180px_120px]">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name, email, registration no." />
        </div>
        <select value={status} onChange={(event) => setStatus(event.target.value)} className="h-10 rounded-md border border-slate-300 px-3 text-sm">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="graduated">Graduated</option>
        </select>
        <Button onClick={load}>Filter</Button>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {loading ? <p className="py-8 text-center text-sm text-slate-500">Loading students...</p> : null}
      {!loading && !students.length ? <p className="py-8 text-center text-sm text-slate-500">No students have been registered yet. Click Register Student to add your first student.</p> : null}
      {students.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-3">Registration No.</th>
                <th className="px-3 py-3">Student</th>
                <th className="px-3 py-3">Grade / Form</th>
                <th className="px-3 py-3">Class / Stream</th>
                <th className="px-3 py-3 text-center"># Subjects</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {students.map((student) => (
                <tr key={student.id}>
                  <td className="px-3 py-3 font-semibold">{student.registrationNumber}</td>
                  <td className="px-3 py-3">
                    <p className="font-medium">{student.name}</p>
                    <p className="text-xs text-slate-500">{student.email ?? student.phone ?? "-"}</p>
                  </td>
                  <td className="px-3 py-3">{student.gradeForm ?? "-"}</td>
                  <td className="px-3 py-3">{student.classStream ?? student.class ?? "Unassigned"}</td>
                  <td className="px-3 py-3 text-center">{student.numberOfSubjects ?? student.subjects?.length ?? "-"}</td>
                  <td className="px-3 py-3"><span className="rounded-full bg-teal-50 px-2 py-1 text-xs font-semibold text-brand">{student.status}</span></td>
                  <td className="px-3 py-3 text-right">
                    <Link className="inline-flex rounded-md p-2" href={`/admin/students/${student.id}`} aria-label="View profile"><Eye className="h-4 w-4" /></Link>
                    <button className="rounded-md p-2" aria-label="Edit"><Edit className="h-4 w-4" /></button>
                    <button onClick={() => deactivate(student.id)} className="rounded-md p-2 text-coral" aria-label="Deactivate"><Trash2 className="h-4 w-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </Card>
  );
}
