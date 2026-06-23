"use client";

import { Check, Copy, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type SubjectOption = { id: number; name: string; code?: string };
type ClassOption = { id: number; name: string; gradeLevel?: string; stream?: string | null; classTeacher?: string | null; classTeacherId?: number | null };
type Assignment = { classId?: number | null; className?: string; subjectId: number };
type Teacher = {
  id: number;
  email: string;
  name: string;
  employeeNumber: string;
  assignments?: { classId: number; subjectId: number; className: string; subjectName: string; subjectCode: string }[];
  classTeacherOf?: { id: number; name: string }[];
};

export function TeacherForm({ teacherId }: { teacherId?: number }) {
  const [subjects, setSubjects] = useState<SubjectOption[]>([]);
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [draftClassName, setDraftClassName] = useState("");
  const [draftSubjectIds, setDraftSubjectIds] = useState<number[]>([]);
  const [makeClassTeacher, setMakeClassTeacher] = useState(false);
  const [classTeacherId, setClassTeacherId] = useState("");
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const selectedClassTeacher = useMemo(
    () => classes.find((item) => item.id === Number(classTeacherId)),
    [classes, classTeacherId]
  );

  useEffect(() => {
    Promise.all([
      api<{ subjects: SubjectOption[]; classes: ClassOption[] }>("/admin/teacher-form-options"),
      teacherId ? api<{ item: Teacher }>(`/admin/teachers/${teacherId}`) : Promise.resolve(null)
    ]).then(([options, result]) => {
      setSubjects(options.subjects);
      setClasses(options.classes);
      if (result) {
        setTeacher(result.item);
        setAssignments((result.item.assignments ?? []).map((item) => ({ classId: item.classId, className: item.className, subjectId: item.subjectId })));
        const assignedClassTeacher = result.item.classTeacherOf?.[0];
        setMakeClassTeacher(Boolean(assignedClassTeacher));
        setClassTeacherId(assignedClassTeacher ? String(assignedClassTeacher.id) : "");
      }
    }).catch((err) => setError(err instanceof Error ? err.message : "Unable to load teacher form"));
  }, [teacherId]);

  function addAssignment() {
    const className = draftClassName.trim();
    const existingClass = classes.find((item) => item.name.toLowerCase() === className.toLowerCase());
    if (!className || !draftSubjectIds.length) {
      setError("Type a class and select at least one subject before adding assignments.");
      return;
    }
    const nextAssignments = draftSubjectIds.map((subjectId) => ({
      classId: existingClass?.id ?? null,
      className,
      subjectId,
    }));
    const duplicate = nextAssignments.find((assignment) =>
      assignments.some((item) => (item.classId || item.className?.toLowerCase()) === (assignment.classId || assignment.className.toLowerCase()) && item.subjectId === assignment.subjectId)
    );
    if (duplicate) {
      setError("One or more selected class-subject assignments have already been added.");
      return;
    }
    setAssignments((current) => [...current, ...nextAssignments]);
    setDraftClassName("");
    setDraftSubjectIds([]);
    setError("");
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      const response = await api<{ item: Teacher; temporaryPassword?: string }>(
        teacherId ? `/admin/teachers/${teacherId}` : "/admin/teachers",
        {
          method: teacherId ? "PUT" : "POST",
          body: JSON.stringify({
            ...values,
            assignments,
            classTeacherId: makeClassTeacher && classTeacherId ? Number(classTeacherId) : null,
          })
        }
      );
      setTeacher(response.item);
      setAssignments((response.item.assignments ?? []).map((item) => ({ classId: item.classId, className: item.className, subjectId: item.subjectId })));
      setTemporaryPassword(response.temporaryPassword ?? "");
      if (!teacherId) {
        form.reset();
        setAssignments([]);
        setMakeClassTeacher(false);
        setClassTeacherId("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save teacher");
    } finally {
      setLoading(false);
    }
  }

  async function copyPassword() {
    await navigator.clipboard.writeText(temporaryPassword);
    setCopied(true);
  }

  return (
    <div className="space-y-5">
      {temporaryPassword ? (
        <Card className="border-teal-200 bg-teal-50">
          <h2 className="font-semibold">Teacher account created successfully.</h2>
          <p className="mt-2 text-sm">Email: <span className="font-semibold">{teacher?.email}</span></p>
          <div className="mt-2 flex items-center gap-2">
            <code className="rounded-md border border-teal-200 bg-white px-3 py-2 font-semibold">{temporaryPassword}</code>
            <button type="button" onClick={copyPassword} className="rounded-md border border-teal-200 bg-white p-2" aria-label="Copy temporary password">
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
          <p className="mt-2 text-sm font-semibold text-coral">Copy this password now. It will not be shown again.</p>
          <p className="mt-1 text-sm text-slate-600">The teacher must change this password on first login.</p>
        </Card>
      ) : null}

      <Card>
        <form onSubmit={submit} className="space-y-6">
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Personal Information</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <Field name="firstName" label="First name" required defaultValue={(teacher as any)?.firstName} />
              <Field name="middleName" label="Middle name" defaultValue={(teacher as any)?.middleName} />
              <Field name="lastName" label="Last name" required defaultValue={(teacher as any)?.lastName} />
              <Select name="gender" label="Gender" options={["Female", "Male", "Other"]} defaultValue={(teacher as any)?.gender} />
              <Field name="nationalId" label="National ID" defaultValue={(teacher as any)?.nationalId} />
              <Field name="phone" label="Phone" defaultValue={(teacher as any)?.phone} />
              <Field name="qualification" label="Qualification" defaultValue={(teacher as any)?.qualification} />
              <Field name="department" label="Department" defaultValue={(teacher as any)?.department} />
              <Field name="specialization" label="Specialization" defaultValue={(teacher as any)?.specialization} />
              <Field name="hireDate" label="Hire date" type="date" defaultValue={(teacher as any)?.hireDate} />
              <Select name="employmentStatus" label="Employment status" options={["Active", "Inactive", "Suspended"]} defaultValue={(teacher as any)?.employmentStatus ?? "Active"} />
              <label className="space-y-1 text-sm font-medium md:col-span-3">Address<textarea name="address" defaultValue={(teacher as any)?.address} className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" /></label>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Account Information</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <Field name="email" label="Email used as login username" type="email" required defaultValue={teacher?.email} />
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">Role is automatically Teacher. A secure default password is generated on creation and must be changed on first login.</div>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Teaching Assignments</h2>
            <div className="grid gap-3 md:grid-cols-[1fr_1.4fr_160px]">
              <label className="space-y-1 text-sm font-medium">
                Class
                <Input list="teacher-class-options" value={draftClassName} onChange={(event) => setDraftClassName(event.target.value)} placeholder="Type class, e.g. Form 1A" />
                <datalist id="teacher-class-options">
                  {classes.map((item) => <option key={item.id} value={item.name}>{item.stream ? `${item.name} - ${item.stream}` : item.name}</option>)}
                </datalist>
              </label>
              <MultiSubjectSelect subjects={subjects} selectedIds={draftSubjectIds} onChange={setDraftSubjectIds} />
              <div className="flex items-end"><Button type="button" onClick={addAssignment} className="w-full"><Plus className="h-4 w-4" /> Add Assignment</Button></div>
            </div>
            <AssignmentTable assignments={assignments} classes={classes} subjects={subjects} onRemove={(assignment) => setAssignments((current) => current.filter((item) => item !== assignment))} />
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Assign as Class Teacher</h2>
            <label className="flex items-center gap-2 text-sm font-medium"><input type="checkbox" checked={makeClassTeacher} onChange={(event) => setMakeClassTeacher(event.target.checked)} /> Make this teacher a class teacher</label>
            {makeClassTeacher ? (
              <div className="grid gap-3 md:grid-cols-2">
                <SelectBox value={classTeacherId} onChange={setClassTeacherId} label="Class teacher class" placeholder="Select class" options={classes.map((item) => ({ id: item.id, label: item.name }))} />
                {selectedClassTeacher?.classTeacher && selectedClassTeacher.classTeacherId !== teacherId ? (
                  <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">This class already has a class teacher: {selectedClassTeacher.classTeacher}. Saving will replace them.</p>
                ) : null}
              </div>
            ) : null}
          </section>

          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <div className="flex justify-end"><Button disabled={loading}>{loading ? "Saving..." : teacherId ? "Update Teacher" : "Create Teacher Account"}</Button></div>
        </form>
      </Card>
    </div>
  );
}

function Field({ name, label, type = "text", required, defaultValue }: { name: string; label: string; type?: string; required?: boolean; defaultValue?: string }) {
  return <label className="space-y-1 text-sm font-medium">{label}{required ? <span className="text-coral"> *</span> : null}<Input key={defaultValue} name={name} type={type} required={required} defaultValue={defaultValue ?? ""} /></label>;
}

function Select({ name, label, options, defaultValue }: { name: string; label: string; options: string[]; defaultValue?: string }) {
  return <label className="space-y-1 text-sm font-medium">{label}<select key={defaultValue} name={name} defaultValue={defaultValue ?? ""} className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm"><option value="">Select</option>{options.map((option) => <option key={option}>{option}</option>)}</select></label>;
}

function SelectBox({ label, placeholder, value, onChange, options }: { label: string; placeholder: string; value: string; onChange: (value: string) => void; options: { id: number; label: string }[] }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm">
        <option value="">{placeholder}</option>
        {options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
      </select>
    </label>
  );
}

function MultiSubjectSelect({ subjects, selectedIds, onChange }: { subjects: SubjectOption[]; selectedIds: number[]; onChange: (ids: number[]) => void }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      Subjects
      <select
        multiple
        value={selectedIds.map(String)}
        onChange={(event) => onChange(Array.from(event.currentTarget.selectedOptions, (option) => Number(option.value)))}
        className="min-h-32 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
      >
        {subjects.map((item) => <option key={item.id} value={item.id}>{item.code ? `${item.code} - ` : ""}{item.name}</option>)}
      </select>
      <span className="text-xs text-slate-500">{selectedIds.length} selected</span>
    </label>
  );
}

function AssignmentTable({ assignments, classes, subjects, onRemove }: { assignments: Assignment[]; classes: ClassOption[]; subjects: SubjectOption[]; onRemove: (assignment: Assignment) => void }) {
  if (!assignments.length) return <p className="rounded-md bg-slate-50 px-3 py-3 text-sm text-slate-500">No teaching assignments added yet.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-3">Class</th><th className="px-3 py-3">Subject</th><th className="px-3 py-3 text-right">Action</th></tr></thead>
        <tbody className="divide-y divide-slate-100">
          {assignments.map((assignment) => {
            const schoolClass = classes.find((item) => item.id === assignment.classId);
            const subject = subjects.find((item) => item.id === assignment.subjectId);
            return (
              <tr key={`${assignment.classId ?? assignment.className}-${assignment.subjectId}`}>
                <td className="px-3 py-3">{schoolClass?.name ?? assignment.className ?? assignment.classId}</td>
                <td className="px-3 py-3">{subject ? `${subject.code ? `${subject.code} - ` : ""}${subject.name}` : assignment.subjectId}</td>
                <td className="px-3 py-3 text-right"><button type="button" onClick={() => onRemove(assignment)} className="rounded-md p-2 text-coral"><Trash2 className="h-4 w-4" /></button></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
