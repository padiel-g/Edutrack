"use client";

import { BookOpen, Check, ChevronDown, Plus, Trash2, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Subject = { id: number; code: string; name: string };
type Teacher = { id: number; name: string; employeeNumber: string };
type SchoolClass = {
  id: number; name: string; gradeLevel: number; capacity: number;
  subjects: Subject[]; teachers?: Teacher[];
  classTeacherId?: number | null;
};
type ManualSubject = { name: string; code: string; stream: string };

export function ClassesManager() {
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [selectedTeacherIds, setSelectedTeacherIds] = useState<number[]>([]);
  const [classTeacherId, setClassTeacherId] = useState("");
  const [selectedSubjectIds, setSelectedSubjectIds] = useState<number[]>([]);
  const [newClassTeacherIds, setNewClassTeacherIds] = useState<number[]>([]);
  const [teacherSubjectAssignments, setTeacherSubjectAssignments] = useState<Record<number, number[]>>({});
  const [newClassTeacherId, setNewClassTeacherId] = useState("");
  const [manualSubjects, setManualSubjects] = useState<ManualSubject[]>([]);
  const [showAddClass, setShowAddClass] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const selectedClass = useMemo(
    () => classes.find((item) => item.id === selectedClassId) ?? null,
    [classes, selectedClassId]
  );

  async function load(preferredClassId?: number) {
    const [classResponse, subjectResponse, teacherResponse] = await Promise.all([
      api<{ items: SchoolClass[] }>("/classes?perPage=100"),
      api<{ items: Subject[] }>("/subjects?perPage=100"),
      api<{ items: Teacher[] }>("/admin/teachers?perPage=100&status=Active")
    ]);
    const ordered = [...classResponse.items].sort((a, b) => a.gradeLevel - b.gradeLevel || a.name.localeCompare(b.name));
    setClasses(ordered);
    setSubjects(subjectResponse.items);
    setTeachers(teacherResponse.items);
    const nextId = preferredClassId ?? selectedClassId ?? ordered[0]?.id ?? null;
    setSelectedClassId(nextId);
    const active = ordered.find((item) => item.id === nextId);
    setSelectedTeacherIds(active?.teachers?.map((teacher) => teacher.id) ?? []);
    setClassTeacherId(active?.classTeacherId ? String(active.classTeacherId) : "");
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load classes"));
  }, []);

  function selectClass(schoolClass: SchoolClass) {
    setSelectedClassId(schoolClass.id);
    setSelectedTeacherIds(schoolClass.teachers?.map((teacher) => teacher.id) ?? []);
    setClassTeacherId(schoolClass.classTeacherId ? String(schoolClass.classTeacherId) : "");
    setError("");
  }

  function toggleTeacher(teacherId: number) {
    setSelectedTeacherIds((current) =>
      current.includes(teacherId) ? current.filter((id) => id !== teacherId) : [...current, teacherId]
    );
  }

  async function saveAssignments() {
    if (!selectedClass) return;
    setSaving(true);
    setError("");
    try {
      const finalTeacherIds = classTeacherId
        ? Array.from(new Set([...selectedTeacherIds, Number(classTeacherId)]))
        : selectedTeacherIds;
      await api(`/admin/classes/${selectedClass.id}/class-teacher`, {
        method: "PUT",
        body: JSON.stringify({ teacherId: classTeacherId ? Number(classTeacherId) : null })
      });
      await api(`/admin/classes/${selectedClass.id}/teachers`, {
        method: "PUT",
        body: JSON.stringify({ teacherIds: finalTeacherIds })
      });
      await load(selectedClass.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save teacher assignments");
    } finally {
      setSaving(false);
    }
  }

  async function createClass(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      const response = await api<{ item: SchoolClass }>("/classes", {
        method: "POST",
        body: JSON.stringify({
          name: form.get("name"),
          gradeLevel: Number(form.get("gradeLevel")),
          capacity: Number(form.get("capacity")),
          subjectIds: selectedSubjectIds,
          teacherIds: newClassTeacherIds,
          classTeacherId: newClassTeacherId ? Number(newClassTeacherId) : null,
          teacherSubjectAssignments: newClassTeacherIds.map((teacherId) => ({
            teacherId,
            subjectIds: teacherSubjectAssignments[teacherId] ?? []
          })),
          manualSubjects: manualSubjects.filter((item) => item.name.trim() || item.code.trim())
        })
      });
      formElement.reset();
      setSelectedSubjectIds([]);
      setNewClassTeacherIds([]);
      setTeacherSubjectAssignments({});
      setNewClassTeacherId("");
      setManualSubjects([]);
      setShowAddClass(false);
      await load(response.item.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create class");
    } finally {
      setSaving(false);
    }
  }

  async function deleteClass() {
    if (!selectedClass || !window.confirm(`Delete ${selectedClass.name}? This cannot be undone.`)) return;
    setDeleting(true);
    setError("");
    try {
      await api(`/classes/${selectedClass.id}`, { method: "DELETE" });
      const remaining = classes.filter((item) => item.id !== selectedClass.id);
      setClasses(remaining);
      const next = remaining[0] ?? null;
      setSelectedClassId(next?.id ?? null);
      setSelectedTeacherIds(next?.teachers?.map((teacher) => teacher.id) ?? []);
      setClassTeacherId(next?.classTeacherId ? String(next.classTeacherId) : "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete class");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[300px_1fr]">
        <Card className="h-fit">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">School Classes</h2>
              <p className="mt-1 text-xs text-slate-500">{classes.length} classes available</p>
            </div>
            <button onClick={() => setShowAddClass((value) => !value)} className="grid h-9 w-9 place-items-center rounded-lg bg-brand text-white" aria-label="Add class">
              <Plus className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-4 space-y-2">
            {!classes.length ? <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">No classes found. Add Form 1 to Form 6 to begin.</p> : null}
            {classes.map((schoolClass) => (
              <button
                key={schoolClass.id}
                onClick={() => selectClass(schoolClass)}
                className={`w-full rounded-xl border p-3 text-left transition ${selectedClassId === schoolClass.id ? "border-brand bg-teal-50" : "border-slate-200 hover:border-slate-300"}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{schoolClass.name}</span>
                  <ChevronDown className={`h-4 w-4 ${selectedClassId === schoolClass.id ? "-rotate-90 text-brand" : "text-slate-400"}`} />
                </div>
                <div className="mt-2 flex gap-3 text-xs text-slate-500">
                  <span>{schoolClass.teachers?.length ?? 0} teachers</span>
                  <span>{schoolClass.subjects?.length ?? 0} subjects</span>
                </div>
              </button>
            ))}
          </div>
        </Card>

        <Card>
          {!selectedClass ? (
            <div className="grid min-h-72 place-items-center text-center">
              <div><BookOpen className="mx-auto h-10 w-10 text-slate-300" /><p className="mt-3 text-slate-500">Select or add a class to manage its teachers.</p></div>
            </div>
          ) : (
            <div>
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-brand">Class management</p>
                  <h2 className="mt-1 text-2xl font-bold">{selectedClass.name}</h2>
                  <p className="mt-1 text-sm text-slate-500">Grade {selectedClass.gradeLevel} · Capacity {selectedClass.capacity}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-slate-50 px-4 py-3 text-right">
                    <p className="text-xs text-slate-500">Teaching staff</p>
                    <p className="text-xl font-bold">{selectedTeacherIds.length}</p>
                  </div>
                  <button
                    type="button"
                    onClick={deleteClass}
                    disabled={deleting}
                    className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    {deleting ? "Deleting..." : "Delete Class"}
                  </button>
                </div>
              </div>

              <div className="mt-5 grid gap-6 lg:grid-cols-[1fr_300px]">
                <section>
                  <div className="flex items-center gap-2"><Users className="h-5 w-5 text-brand" /><h3 className="font-semibold">Assign teachers</h3></div>
                  <p className="mt-1 text-sm text-slate-500">Choose all teachers who teach {selectedClass.name}.</p>
                  <div className="mt-4 grid gap-2 sm:grid-cols-2">
                    {teachers.map((teacher) => {
                      const checked = selectedTeacherIds.includes(teacher.id) || classTeacherId === String(teacher.id);
                      return (
                        <button key={teacher.id} type="button" onClick={() => toggleTeacher(teacher.id)} className={`flex items-center gap-3 rounded-xl border p-3 text-left ${checked ? "border-brand bg-teal-50" : "border-slate-200"}`}>
                          <span className={`grid h-5 w-5 place-items-center rounded border ${checked ? "border-brand bg-brand text-white" : "border-slate-300"}`}>{checked ? <Check className="h-3.5 w-3.5" /> : null}</span>
                          <span><span className="block text-sm font-semibold">{teacher.name}</span><span className="text-xs text-slate-500">{teacher.employeeNumber}</span></span>
                        </button>
                      );
                    })}
                  </div>
                </section>

                <section className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="font-semibold">Class Teacher</h3>
                  <p className="mt-1 text-xs text-slate-500">Only one Class Teacher can be selected.</p>
                  <select value={classTeacherId} onChange={(event) => setClassTeacherId(event.target.value)} className="mt-4 h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm">
                    <option value="">Not assigned</option>
                    {teachers.map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.employeeNumber} - {teacher.name}</option>)}
                  </select>
                  <Button className="mt-4 w-full" onClick={saveAssignments} disabled={saving}>{saving ? "Saving..." : "Save Assignments"}</Button>
                </section>
              </div>
            </div>
          )}
        </Card>
      </div>

      {showAddClass ? (
        <Card>
          <div className="flex items-center justify-between"><div><h2 className="text-lg font-semibold">Add a Class</h2><p className="text-sm text-slate-500">Create Form 1, Form 2, Form 3 through Form 6.</p></div><button onClick={() => setShowAddClass(false)} className="text-sm text-slate-500">Close</button></div>
          <form onSubmit={createClass} className="mt-5 grid gap-4 lg:grid-cols-4">
            <label className="space-y-1 text-sm font-medium">Class name <span className="text-coral">*</span><Input name="name" placeholder="e.g. Form 3" required /></label>
            <label className="space-y-1 text-sm font-medium">
              Grade level <span className="text-coral">*</span>
              <select name="gradeLevel" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                <option value="">Select form</option>
                {[1, 2, 3, 4, 5, 6].map((form) => <option key={form} value={form}>Form {form}</option>)}
              </select>
            </label>
            <label className="space-y-1 text-sm font-medium">Capacity<Input name="capacity" type="number" min="1" defaultValue="35" /></label>
            <div className="flex items-end"><Button className="w-full" disabled={saving}>{saving ? "Saving..." : "Create Class"}</Button></div>
            <label className="space-y-1 text-sm font-medium lg:col-span-2">Subjects
              <select multiple value={selectedSubjectIds.map(String)} onChange={(event) => setSelectedSubjectIds(Array.from(event.target.selectedOptions, (option) => Number(option.value)))} className="min-h-28 w-full rounded-md border border-slate-300 bg-white p-2 text-sm">
                {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.code} - {subject.name}</option>)}
              </select>
            </label>
            <div className="space-y-2 lg:col-span-2">
              <button type="button" onClick={() => setManualSubjects((current) => [...current, { name: "", code: "", stream: "" }])} className="inline-flex items-center gap-1 text-sm font-semibold text-brand"><Plus className="h-4 w-4" /> Add a new subject</button>
              {manualSubjects.map((subject, index) => (
                <div key={index} className="grid grid-cols-[1fr_110px_36px] gap-2">
                  <Input value={subject.name} onChange={(event) => setManualSubjects((current) => current.map((item, i) => i === index ? { ...item, name: event.target.value } : item))} placeholder="Subject name" />
                  <Input value={subject.code} onChange={(event) => setManualSubjects((current) => current.map((item, i) => i === index ? { ...item, code: event.target.value } : item))} placeholder="Code" />
                  <button type="button" onClick={() => setManualSubjects((current) => current.filter((_, i) => i !== index))} className="grid place-items-center text-coral"><Trash2 className="h-4 w-4" /></button>
                </div>
              ))}
            </div>
            <div className="space-y-2 lg:col-span-2">
              <p className="text-sm font-medium">Assign teachers</p>
              <p className="text-xs text-slate-500">Choose one or more teachers who will teach this class.</p>
              <div className="grid max-h-48 gap-2 overflow-y-auto rounded-lg border border-slate-200 p-2 sm:grid-cols-2">
                {teachers.map((teacher) => {
                  const selected = newClassTeacherIds.includes(teacher.id) || newClassTeacherId === String(teacher.id);
                  return (
                    <button
                      key={teacher.id}
                      type="button"
                      onClick={() => setNewClassTeacherIds((current) =>
                        current.includes(teacher.id)
                          ? current.filter((id) => id !== teacher.id)
                          : [...current, teacher.id]
                      )}
                      className={`flex items-center gap-2 rounded-lg border p-2 text-left ${selected ? "border-brand bg-teal-50" : "border-slate-200"}`}
                    >
                      <span className={`grid h-5 w-5 place-items-center rounded border ${selected ? "border-brand bg-brand text-white" : "border-slate-300"}`}>
                        {selected ? <Check className="h-3.5 w-3.5" /> : null}
                      </span>
                      <span><span className="block text-sm font-semibold">{teacher.name}</span><span className="text-xs text-slate-500">{teacher.employeeNumber}</span></span>
                    </button>
                  );
                })}
                {!teachers.length ? <p className="p-2 text-sm text-slate-500">No active teachers found.</p> : null}
              </div>
              {newClassTeacherIds.map((teacherId) => {
                const teacher = teachers.find((item) => item.id === teacherId);
                const assigned = teacherSubjectAssignments[teacherId] ?? [];
                return (
                  <div key={teacherId} className="rounded-lg border border-slate-200 p-3">
                    <p className="text-sm font-semibold">{teacher?.name}</p>
                    <p className="mb-2 text-xs text-slate-500">Select subjects this teacher will teach in this class.</p>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {subjects.filter((subject) => selectedSubjectIds.includes(subject.id)).map((subject) => {
                        const checked = assigned.includes(subject.id);
                        return (
                          <button
                            key={subject.id}
                            type="button"
                            onClick={() => setTeacherSubjectAssignments((current) => ({
                              ...current,
                              [teacherId]: checked
                                ? assigned.filter((id) => id !== subject.id)
                                : [...assigned, subject.id]
                            }))}
                            className={`flex items-center gap-2 rounded-md border p-2 text-left text-xs ${checked ? "border-brand bg-teal-50" : "border-slate-200"}`}
                          >
                            <span className={`grid h-4 w-4 place-items-center rounded border ${checked ? "border-brand bg-brand text-white" : "border-slate-300"}`}>
                              {checked ? <Check className="h-3 w-3" /> : null}
                            </span>
                            {subject.code} - {subject.name}
                          </button>
                        );
                      })}
                      {!selectedSubjectIds.length ? <p className="text-xs text-slate-500">Select class subjects above first.</p> : null}
                    </div>
                  </div>
                );
              })}
            </div>
            <label className="space-y-1 text-sm font-medium lg:col-span-2">
              Class Teacher
              <select
                value={newClassTeacherId}
                onChange={(event) => {
                  setNewClassTeacherId(event.target.value);
                  if (event.target.value) {
                    setNewClassTeacherIds((current) => Array.from(new Set([...current, Number(event.target.value)])));
                  }
                }}
                className="h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
              >
                <option value="">Not assigned</option>
                {teachers.map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.employeeNumber} - {teacher.name}</option>)}
              </select>
              <span className="block text-xs font-normal text-slate-500">Only one Class Teacher can be selected.</span>
            </label>
          </form>
        </Card>
      ) : null}
      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
