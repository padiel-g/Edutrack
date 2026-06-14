"use client";

import { Check, Copy } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Option = { id: number; name: string; code?: string };
type Teacher = {
  id: number; email: string; name: string; employeeNumber: string;
  subjects: Option[]; classes: Option[]; classTeacherOf?: Option[];
};

export function TeacherForm({ teacherId }: { teacherId?: number }) {
  const [subjects, setSubjects] = useState<Option[]>([]);
  const [classes, setClasses] = useState<Option[]>([]);
  const [selectedSubjects, setSelectedSubjects] = useState<number[]>([]);
  const [selectedClasses, setSelectedClasses] = useState<number[]>([]);
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api<{ subjects: Option[]; classes: Option[] }>("/admin/teacher-form-options"),
      teacherId ? api<{ item: Teacher }>(`/admin/teachers/${teacherId}`) : Promise.resolve(null)
    ]).then(([options, result]) => {
      setSubjects(options.subjects);
      setClasses(options.classes);
      if (result) {
        setTeacher(result.item);
        setSelectedSubjects(result.item.subjects.map((item) => item.id));
        setSelectedClasses(result.item.classes.map((item) => item.id));
      }
    }).catch((err) => setError(err instanceof Error ? err.message : "Unable to load teacher form"));
  }, [teacherId]);

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
          body: JSON.stringify({ ...values, subjectIds: selectedSubjects, classIds: selectedClasses })
        }
      );
      setTeacher(response.item);
      setTemporaryPassword(response.temporaryPassword ?? "");
      if (!teacherId) form.reset();
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
          <div className="grid gap-4 md:grid-cols-3">
            <Field name="firstName" label="First name" required defaultValue={(teacher as any)?.firstName} />
            <Field name="middleName" label="Middle name" defaultValue={(teacher as any)?.middleName} />
            <Field name="lastName" label="Last name" required defaultValue={(teacher as any)?.lastName} />
            <Select name="gender" label="Gender" options={["Female", "Male", "Other"]} defaultValue={(teacher as any)?.gender} />
            <Field name="nationalId" label="National ID" defaultValue={(teacher as any)?.nationalId} />
            <Field name="email" label="Email" type="email" required defaultValue={teacher?.email} />
            <Field name="phone" label="Phone" defaultValue={(teacher as any)?.phone} />
            <Field name="qualification" label="Qualification" defaultValue={(teacher as any)?.qualification} />
            <Field name="department" label="Department" defaultValue={(teacher as any)?.department} />
            <Field name="specialization" label="Specialization" defaultValue={(teacher as any)?.specialization} />
            <Field name="hireDate" label="Hire date" type="date" defaultValue={(teacher as any)?.hireDate} />
            <Select name="employmentStatus" label="Employment status" options={["Active", "Inactive", "Suspended"]} defaultValue={(teacher as any)?.employmentStatus ?? "Active"} />
            <label className="space-y-1 text-sm font-medium md:col-span-3">Address<textarea name="address" defaultValue={(teacher as any)?.address} className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" /></label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <MultiSelect label="Assigned subjects" options={subjects} values={selectedSubjects} onChange={setSelectedSubjects} />
            <div className="space-y-2">
              <MultiSelect
                label="Classes the teacher will teach"
                options={classes}
                values={selectedClasses}
                onChange={setSelectedClasses}
              />
              {teacher?.classTeacherOf?.length ? (
                <p className="rounded-md bg-teal-50 px-3 py-2 text-xs text-teal-700">
                  <span className="font-semibold">Class Teacher of:</span>{" "}
                  {teacher.classTeacherOf.map((item) => item.name).join(", ")}
                </p>
              ) : null}
              <p className="text-xs text-slate-500">
                Use the Classes page to designate this teacher as the Class Teacher of a class.
              </p>
            </div>
          </div>
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

function MultiSelect({ label, options, values, onChange }: { label: string; options: Option[]; values: number[]; onChange: (values: number[]) => void }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      {label}
      <select multiple value={values.map(String)} onChange={(event) => onChange(Array.from(event.target.selectedOptions, (option) => Number(option.value)))} className="min-h-40 w-full rounded-md border border-slate-300 p-2 text-sm">
        {options.map((option) => <option key={option.id} value={option.id}>{option.code ? `${option.code} - ` : ""}{option.name}</option>)}
      </select>
      <span className="block text-xs font-normal text-slate-500">Hold Ctrl to select multiple entries.</span>
    </label>
  );
}
