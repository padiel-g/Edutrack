"use client";

import { Check, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Subject = { id: number; code: string; name: string };
type Teacher = { id: number; employeeNumber: string; name: string };
type SchoolClass = { id: number; name: string };
type LearningEntry = {
  id: number;
  class_id: number;
  subject_id: number;
  teacher_id: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
};

export function LearningTimetableManager() {
  const [entries, setEntries] = useState<LearningEntry[]>([]);
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [selectedSubjectIds, setSelectedSubjectIds] = useState<number[]>([]);
  const [classMode, setClassMode] = useState<"select" | "add">("select");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const [timetable, classResponse, subjectResponse, teacherResponse] = await Promise.all([
      api<{ items: LearningEntry[] }>("/timetables?perPage=100"),
      api<{ items: SchoolClass[] }>("/classes?perPage=100"),
      api<{ items: Subject[] }>("/subjects?perPage=100"),
      api<{ items: Teacher[] }>("/admin/teachers?perPage=100&status=Active")
    ]);
    setEntries(timetable.items);
    setClasses(classResponse.items);
    setSubjects(subjectResponse.items);
    setTeachers(teacherResponse.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load learning timetable"));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      if (!selectedSubjectIds.length) {
        throw new Error("Select at least one subject.");
      }

      let classId = Number(values.classId);
      if (classMode === "add") {
        const classResponse = await api<{ item: SchoolClass }>("/classes", {
          method: "POST",
          body: JSON.stringify({
            name: values.newClassName,
            gradeLevel: Number(values.gradeLevel),
            capacity: Number(values.capacity) || 35,
            subjectIds: selectedSubjectIds,
            teacherIds: [Number(values.teacherId)],
            classTeacherId: null,
            manualSubjects: []
          })
        });
        classId = classResponse.item.id;
      }

      await Promise.all(
        selectedSubjectIds.map((subjectId) =>
          api("/timetables", {
            method: "POST",
            body: JSON.stringify({
              class_id: classId,
              subject_id: subjectId,
              teacher_id: Number(values.teacherId),
              day_of_week: values.dayOfWeek,
              start_time: values.startTime,
              end_time: values.endTime
            })
          })
        )
      );
      form.reset();
      setSelectedSubjectIds([]);
      setClassMode("select");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create learning timetable entry");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    if (!window.confirm("Delete this learning timetable entry?")) return;
    try {
      await api(`/timetables/${id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete timetable entry");
    }
  }

  const className = (id: number) => classes.find((item) => item.id === id)?.name ?? "-";
  const subjectName = (id: number) => subjects.find((item) => item.id === id)?.name ?? "-";
  const teacherName = (id: number) => teachers.find((item) => item.id === id)?.name ?? "-";
  const allSubjectsSelected = subjects.length > 0 && selectedSubjectIds.length === subjects.length;

  function toggleSubject(subjectId: number) {
    setSelectedSubjectIds((current) =>
      current.includes(subjectId)
        ? current.filter((id) => id !== subjectId)
        : [...current, subjectId]
    );
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
      <Card>
        <h2 className="text-lg font-semibold">Learning Timetable</h2>
        {!entries.length ? (
          <p className="py-8 text-center text-sm text-slate-500">No learning timetable has been created yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-3">Day</th>
                  <th className="px-3 py-3">Class</th>
                  <th className="px-3 py-3">Subject</th>
                  <th className="px-3 py-3">Teacher</th>
                  <th className="px-3 py-3">Time</th>
                  <th className="px-3 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-3 py-3 font-medium">{entry.day_of_week}</td>
                    <td className="px-3 py-3">{className(entry.class_id)}</td>
                    <td className="px-3 py-3">{subjectName(entry.subject_id)}</td>
                    <td className="px-3 py-3">{teacherName(entry.teacher_id)}</td>
                    <td className="px-3 py-3">{entry.start_time} - {entry.end_time}</td>
                    <td className="px-3 py-3 text-right">
                      <button onClick={() => remove(entry.id)} className="rounded-md p-2 text-coral" aria-label="Delete learning timetable entry">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="text-lg font-semibold">Create Learning Entry</h2>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <label className="block space-y-1 text-sm font-medium">Day
            <select name="dayOfWeek" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              <option value="">Select day</option>
              {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].map((day) => <option key={day}>{day}</option>)}
            </select>
          </label>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Class</span>
              <button
                type="button"
                onClick={() => setClassMode((current) => current === "select" ? "add" : "select")}
                className="inline-flex items-center gap-1 text-xs font-semibold text-brand"
              >
                <Plus className="h-3.5 w-3.5" />
                {classMode === "select" ? "Add new class" : "Select existing"}
              </button>
            </div>
            {classMode === "select" ? (
              <select name="classId" required className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                <option value="">Select class</option>
                {classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            ) : (
              <div className="mt-2 grid gap-3 sm:grid-cols-2">
                <label className="space-y-1 text-sm font-medium sm:col-span-2">Class name<Input name="newClassName" placeholder="e.g. Form 4 East" required /></label>
                <label className="space-y-1 text-sm font-medium">Grade level<Input name="gradeLevel" type="number" min="1" max="6" required /></label>
                <label className="space-y-1 text-sm font-medium">Capacity<Input name="capacity" type="number" min="1" defaultValue="35" /></label>
              </div>
            )}
          </div>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Subjects</span>
              <button
                type="button"
                onClick={() => setSelectedSubjectIds(allSubjectsSelected ? [] : subjects.map((item) => item.id))}
                className="text-xs font-semibold text-brand"
              >
                {allSubjectsSelected ? "Clear all" : "Select all"}
              </button>
            </div>
            <div className="mt-2 grid max-h-52 gap-2 overflow-y-auto rounded-lg border border-slate-200 p-2 sm:grid-cols-2">
              {subjects.map((subject) => {
                const selected = selectedSubjectIds.includes(subject.id);
                return (
                  <button
                    key={subject.id}
                    type="button"
                    onClick={() => toggleSubject(subject.id)}
                    className={`flex items-center gap-2 rounded-lg border p-2 text-left ${selected ? "border-brand bg-teal-50" : "border-slate-200"}`}
                  >
                    <span className={`grid h-5 w-5 shrink-0 place-items-center rounded border ${selected ? "border-brand bg-brand text-white" : "border-slate-300"}`}>
                      {selected ? <Check className="h-3.5 w-3.5" /> : null}
                    </span>
                    <span className="text-sm"><strong>{subject.code}</strong> - {subject.name}</span>
                  </button>
                );
              })}
            </div>
            <p className="mt-1 text-xs text-slate-500">{selectedSubjectIds.length} subject(s) selected</p>
          </div>
          <label className="block space-y-1 text-sm font-medium">Teacher
            <select name="teacherId" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              <option value="">Select teacher</option>
              {teachers.map((item) => <option key={item.id} value={item.id}>{item.employeeNumber} - {item.name}</option>)}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block space-y-1 text-sm font-medium">Start time<Input name="startTime" type="time" required /></label>
            <label className="block space-y-1 text-sm font-medium">End time<Input name="endTime" type="time" required /></label>
          </div>
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button className="w-full" disabled={loading}>{loading ? "Saving..." : `Add ${selectedSubjectIds.length || ""} Learning Period${selectedSubjectIds.length === 1 ? "" : "s"}`}</Button>
        </form>
      </Card>
    </div>
  );
}
