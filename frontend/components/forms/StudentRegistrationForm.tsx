"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import type { Student, StudentSubject } from "@/types/student";

type Options = {
  classes: { id: number; name: string; gradeLevel?: string; stream?: string | null; academicYearId?: number | null; academicYear?: string | null }[];
  academicYears: { id: number; name: string }[];
  parents: { id: number; name: string }[];
  subjects: StudentSubject[];
  gradeForms: string[];
  classStreams: string[];
};

const DEFAULT_OPTIONS: Options = {
  classes: [],
  academicYears: [],
  parents: [],
  subjects: [],
  gradeForms: [],
  classStreams: []
};

export function StudentRegistrationForm() {
  const [options, setOptions] = useState<Options>(DEFAULT_OPTIONS);
  const [created, setCreated] = useState<Student | null>(null);
  const [parentTemporaryPassword, setParentTemporaryPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [className, setClassName] = useState("");
  const [numberOfSubjects, setNumberOfSubjects] = useState<number | "">("");
  const [selectedSubjectIds, setSelectedSubjectIds] = useState<number[]>([]);

  useEffect(() => {
    api<Options>("/admin/student-form-options")
      .then((res) => setOptions({ ...DEFAULT_OPTIONS, ...res }))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load registration options."));
  }, []);

  const selectedClass = useMemo(
    () => options.classes.find((item) => item.name.toLowerCase() === className.trim().toLowerCase()),
    [options.classes, className]
  );

  const visibleSubjects = useMemo(() => {
    const stream = selectedClass?.stream;
    return options.subjects
      .slice()
      .sort((a, b) => {
        const aMatch = stream ? a.stream === stream : false;
        const bMatch = stream ? b.stream === stream : false;
        if (aMatch === bMatch) return a.name.localeCompare(b.name);
        return aMatch ? -1 : 1;
      });
  }, [options.subjects, selectedClass]);

  function toggleSubject(id: number) {
    setSelectedSubjectIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (!expectedCount || prev.length >= expectedCount) return prev;
      return [...prev, id];
    });
  }

  useEffect(() => {
    setSelectedSubjectIds([]);
  }, [className]);

  const expectedCount = typeof numberOfSubjects === "number" ? numberOfSubjects : 0;

  useEffect(() => {
    if (expectedCount > 0) {
      setSelectedSubjectIds((current) => current.slice(0, expectedCount));
    }
  }, [expectedCount]);

  const selectionWarning =
    expectedCount > 0 && selectedSubjectIds.length !== expectedCount
      ? `Selected ${selectedSubjectIds.length} of ${expectedCount} required subjects.`
      : "";

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    const typedClassName = className.trim();
    if (!typedClassName) {
      setLoading(false);
      setError("Type a class before registering the student.");
      return;
    }
    if (!options.subjects.length) {
      setLoading(false);
      setError("Subjects could not be loaded. Refresh the page and try again.");
      return;
    }
    if (!expectedCount || expectedCount <= 0) {
      setLoading(false);
      setError("Number of subjects is required and must be greater than 0.");
      return;
    }
    if (!selectedSubjectIds.length) {
      setLoading(false);
      setError("A student cannot be registered without selecting subjects.");
      return;
    }
    if (new Set(selectedSubjectIds).size !== selectedSubjectIds.length) {
      setLoading(false);
      setError("Duplicate subjects are not allowed for the same student.");
      return;
    }
    if (selectedSubjectIds.length !== expectedCount) {
      setLoading(false);
      setError("Selected subjects must match the number of subjects value.");
      return;
    }

    const formEl = event.currentTarget;
    const form = new FormData(formEl);
    const body = Object.fromEntries(form.entries());

    try {
      const response = await api<{ item: Student; registrationNumber: string; parentTemporaryPassword: string }>("/admin/students", {
        method: "POST",
        body: JSON.stringify({
          ...body,
          academicYearId: body.academicYearId ? Number(body.academicYearId) : undefined,
          parentId: body.parentId ? Number(body.parentId) : undefined,
          classId: selectedClass?.id,
          className: typedClassName,
          numberOfSubjects: expectedCount,
          selectedSubjectIds
        })
      });
      setCreated(response.item);
      setParentTemporaryPassword(response.parentTemporaryPassword);
      formEl.reset();
      setClassName("");
      setNumberOfSubjects("");
      setSelectedSubjectIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to register student");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      {created ? (
        <Card className="border-teal-200 bg-teal-50">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-1 h-5 w-5 text-brand" />
            <div className="space-y-2">
              <div>
                <h2 className="font-semibold">Student registered successfully</h2>
                <p className="text-sm text-slate-600">
                  <span className="font-semibold text-ink">{created.name}</span> has been added to EduTrack.
                </p>
              </div>
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                <SummaryRow label="Registration number" value={created.registrationNumber} />
                <SummaryRow label="Parent temporary password" value={parentTemporaryPassword} />
                <SummaryRow label="Grade / Form" value={created.gradeForm} />
                <SummaryRow label="Class / Stream" value={created.classStream} />
                <SummaryRow label="Number of subjects" value={String(created.numberOfSubjects ?? "-")} />
              </dl>
              {created.subjects?.length ? (
                <div className="text-sm">
                  <p className="font-semibold text-ink">Selected subjects</p>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {created.subjects.map((subject) => (
                      <li
                        key={subject.id}
                        className="rounded-full border border-teal-200 bg-white px-3 py-1 text-xs font-medium text-brand"
                      >
                        {subject.name}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        </Card>
      ) : null}
      <Card>
        <form onSubmit={submit} className="space-y-6">
          <section className="space-y-4">
            <header className="border-b border-slate-200 pb-2">
              <h2 className="text-lg font-semibold">Personal Details</h2>
              <p className="text-xs text-slate-500">Basic student identity information.</p>
            </header>
            <div className="grid gap-4 md:grid-cols-3">
              <Field label="First name" name="firstName" required />
              <Field label="Middle name" name="middleName" />
              <Field label="Last name" name="lastName" required />
              <Select label="Gender" name="gender" options={["Female", "Male", "Other"]} />
              <Field label="Date of birth" name="dateOfBirth" type="date" />
              <Field label="Birth certificate no. (optional)" name="birthCertificateNumber" />
              <Field label="National ID (optional)" name="nationalId" />
              <Field label="Email" name="email" type="email" />
              <Field label="Phone" name="phone" />
            </div>
          </section>

          <section className="space-y-4">
            <header className="border-b border-slate-200 pb-2">
              <h2 className="text-lg font-semibold">Enrollment</h2>
              <p className="text-xs text-slate-500">Class assignment, academic year and guardian linkage.</p>
            </header>
            <div className="grid gap-4 md:grid-cols-3">
              <Field label="Class Type" name="classType" />
              <label className="space-y-1 text-sm font-medium">
                Academic year
                <select name="academicYearId" className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm">
                  <option value="">Select year</option>
                  {options.academicYears.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </label>
              <label className="space-y-1 text-sm font-medium">
                Parent / guardian
                <select name="parentId" className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm">
                  <option value="">Link parent</option>
                  {options.parents.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </label>
              <Field label="Enrollment date" name="enrollmentDate" type="date" />
              <label className="space-y-1 text-sm font-medium md:col-span-2">
                Address
                <textarea name="address" className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
              </label>
            </div>
          </section>

          <section className="space-y-4">
            <header className="border-b border-slate-200 pb-2">
              <h2 className="text-lg font-semibold">Academic Details</h2>
              <p className="text-xs text-slate-500">Choose the Admin-created class and registered subjects.</p>
            </header>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="space-y-1 text-sm font-medium">
                Class <span className="text-coral">*</span>
                <Input list="student-class-options" value={className} onChange={(event) => setClassName(event.target.value)} placeholder="Type class, e.g. Form 1A" required />
                <datalist id="student-class-options">
                  {options.classes.map((item) => <option key={item.id} value={item.name}>{[item.gradeLevel, item.stream, item.academicYear].filter(Boolean).join(" - ")}</option>)}
                </datalist>
              </label>
              <ReadOnlyValue label="Grade / Form" value={selectedClass?.gradeLevel || className.trim()} />
              <ReadOnlyValue label="Stream / Section" value={selectedClass?.stream || selectedClass?.name || className.trim()} />
              <label className="space-y-1 text-sm font-medium">
                Number of subjects <span className="text-coral">*</span>
                <select
                  value={numberOfSubjects}
                  onChange={(event) => setNumberOfSubjects(event.target.value ? Number(event.target.value) : "")}
                  className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm"
                  required
                >
                  <option value="">Select number</option>
                  {Array.from({ length: options.subjects.length }, (_, index) => index + 1).map((count) => (
                    <option key={count} value={count}>{count}</option>
                  ))}
                </select>
              </label>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">
                  Subjects <span className="text-coral">*</span>
                </p>
                <p className="text-xs text-slate-500">
                  {selectedSubjectIds.length} selected{expectedCount ? ` / ${expectedCount} required` : ""}
                </p>
              </div>
              <p className="text-xs text-slate-500">Subjects matching the selected class section are shown first.</p>
              <div className="grid max-h-64 gap-2 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3 sm:grid-cols-2 lg:grid-cols-3">
                {visibleSubjects.length ? (
                  visibleSubjects.map((subject) => {
                    const checked = selectedSubjectIds.includes(subject.id);
                    const suggested = Boolean(selectedClass?.stream && subject.stream === selectedClass.stream);
                    return (
                      <label
                        key={subject.id}
                        className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition ${
                          checked
                            ? "border-brand bg-white shadow-sm"
                            : suggested
                            ? "border-teal-200 bg-white"
                            : "border-slate-200 bg-white/70"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={!checked && (!expectedCount || selectedSubjectIds.length >= expectedCount)}
                          onChange={() => toggleSubject(subject.id)}
                          className="h-4 w-4 accent-teal-600 disabled:opacity-40"
                        />
                        <span className="flex-1">
                          <span className="block font-medium">{subject.name}</span>
                          {subject.stream ? (
                            <span className="text-xs text-slate-500">{subject.stream}</span>
                          ) : null}
                        </span>
                        {suggested ? (
                          <span className="rounded-full bg-teal-50 px-2 py-0.5 text-[10px] font-semibold uppercase text-brand">
                            Suggested
                          </span>
                        ) : null}
                      </label>
                    );
                  })
                ) : (
                  <p className="col-span-full py-4 text-center text-sm text-slate-500">
                    No subjects available. Ask an administrator to add subjects first.
                  </p>
                )}
              </div>
              {selectionWarning ? (
                <p className="text-xs font-medium text-amber-600">{selectionWarning}</p>
              ) : null}
            </div>
          </section>

          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

          <div className="flex justify-end">
            <Button disabled={loading}>{loading ? "Registering..." : "Register Student"}</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function Field(props: { label: string; name: string; type?: string; required?: boolean }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      {props.label}{props.required ? <span className="text-coral"> *</span> : null}
      <Input name={props.name} type={props.type ?? "text"} required={props.required} />
    </label>
  );
}

function Select({ label, name, options }: { label: string; name: string; options: string[] }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      {label}
      <select name={name} className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm">
        <option value="">Select</option>
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}

function ReadOnlyValue({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="space-y-1 text-sm font-medium">
      <p>{label}</p>
      <div className="flex h-10 items-center rounded-md border border-slate-200 bg-slate-50 px-3 text-sm text-slate-600">
        {value || "Selected from class"}
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="font-semibold text-ink">{value || "-"}</dd>
    </div>
  );
}
