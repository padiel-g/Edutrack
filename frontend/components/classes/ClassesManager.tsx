"use client";

import { BookOpen, CalendarDays, Eye, Plus, Search, Trash2, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type AcademicYear = { id: number; name: string };
type SchoolClass = {
  id: number;
  name: string;
  gradeLevel: string;
  stream?: string | null;
  capacity: number;
  academicYearId?: number | null;
  academicYear?: string | null;
  studentCount: number;
  subjectCount: number;
  teacherCount: number;
  enrollment: string;
  classTeacher?: { id: number; name: string } | null;
};
type ClassDetail = {
  item: SchoolClass;
  students: { id: number; registrationNumber: string; name: string; gender?: string; parent?: string | null; status: string }[];
  subjects: { id: number; code: string; name: string; subjectType?: string | null }[];
  teachers: { teacherId: number; teacherName: string; subjectName: string; subjectCode: string; department?: string | null; email: string; phone?: string | null }[];
  classTeacher?: { id: number; name: string; email?: string; phone?: string } | null;
  attendanceSummary: { records: number; present: number; attendanceRate?: number | null };
  performanceSummary: { averageScore?: number | null; examResultCount: number; finalResultCount: number };
};

const gradeOptions = ["ECD", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Form 1", "Form 2", "Form 3", "Form 4", "Lower Six", "Upper Six", "Custom"];
const tabs = ["Overview", "Students", "Subjects", "Teachers", "Attendance Summary", "Performance Summary"] as const;

export function ClassesManager() {
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [detail, setDetail] = useState<ClassDetail | null>(null);
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Overview");
  const [showAddClass, setShowAddClass] = useState(false);
  const [gradeLevel, setGradeLevel] = useState("");
  const [customGrade, setCustomGrade] = useState("");
  const [search, setSearch] = useState("");
  const [filterGrade, setFilterGrade] = useState("");
  const [filterStream, setFilterStream] = useState("");
  const [filterYear, setFilterYear] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const streamOptions = useMemo(
    () => Array.from(new Set(classes.map((item) => item.stream).filter(Boolean) as string[])).sort(),
    [classes]
  );
  const classGradeOptions = useMemo(
    () => Array.from(new Set([...gradeOptions.filter((item) => item !== "Custom"), ...classes.map((item) => item.gradeLevel)])).sort(),
    [classes]
  );

  async function load() {
    const [classResponse, yearResponse] = await Promise.all([
      api<{ items: SchoolClass[] }>("/admin/classes?perPage=100"),
      api<{ items: AcademicYear[] }>("/academic-years?perPage=100"),
    ]);
    setClasses(classResponse.items);
    setYears(yearResponse.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load classes"));
  }, []);

  async function applyFilters() {
    setError("");
    const query = new URLSearchParams();
    if (search) query.set("search", search);
    if (filterGrade) query.set("gradeLevel", filterGrade);
    if (filterStream) query.set("stream", filterStream);
    if (filterYear) query.set("academicYearId", filterYear);
    try {
      const response = await api<{ items: SchoolClass[] }>(`/admin/classes?${query}`);
      setClasses(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to filter classes");
    }
  }

  async function createClass(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const selectedGrade = gradeLevel === "Custom" ? customGrade.trim() : gradeLevel;
    try {
      await api<{ item: SchoolClass }>("/admin/classes", {
        method: "POST",
        body: JSON.stringify({
          name: form.get("name"),
          gradeLevel: selectedGrade,
          stream: form.get("stream"),
          capacity: Number(form.get("capacity") || 35),
          academicYearId: Number(form.get("academicYearId")),
        })
      });
      formElement.reset();
      setGradeLevel("");
      setCustomGrade("");
      setShowAddClass(false);
      setMessage("Class created successfully.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create class");
    } finally {
      setSaving(false);
    }
  }

  async function openDetail(classId: number) {
    setError("");
    try {
      const response = await api<ClassDetail>(`/admin/classes/${classId}`);
      setDetail(response);
      setActiveTab("Overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load class details");
    }
  }

  async function deleteClass(schoolClass: SchoolClass) {
    if (!window.confirm(`Delete ${schoolClass.name}? This only works if no students are assigned.`)) return;
    setDeletingId(schoolClass.id);
    setError("");
    setMessage("");
    try {
      await api(`/admin/classes/${schoolClass.id}`, { method: "DELETE" });
      setClasses((current) => current.filter((item) => item.id !== schoolClass.id));
      if (detail?.item.id === schoolClass.id) setDetail(null);
      setMessage("Class deleted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete class");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-5">
      <Card className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Classes</h2>
            <p className="text-sm text-slate-500">View classes created by Admin and monitor students, subjects, teachers, and class teachers.</p>
          </div>
          <Button onClick={() => setShowAddClass((value) => !value)}><Plus className="h-4 w-4" /> Add Class</Button>
        </div>
        <div className="grid gap-3 lg:grid-cols-[1fr_180px_180px_180px_120px]">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search class name" />
          </div>
          <select value={filterGrade} onChange={(event) => setFilterGrade(event.target.value)} className="h-10 rounded-md border border-slate-300 px-3 text-sm">
            <option value="">All grades/forms</option>
            {classGradeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={filterStream} onChange={(event) => setFilterStream(event.target.value)} className="h-10 rounded-md border border-slate-300 px-3 text-sm">
            <option value="">All sections</option>
            {streamOptions.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={filterYear} onChange={(event) => setFilterYear(event.target.value)} className="h-10 rounded-md border border-slate-300 px-3 text-sm">
            <option value="">All years</option>
            {years.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
          </select>
          <Button onClick={applyFilters}>Filter</Button>
        </div>
      </Card>

      {showAddClass ? (
        <Card>
          <h2 className="text-lg font-semibold">Create Class</h2>
          <form onSubmit={createClass} className="mt-5 grid gap-4 lg:grid-cols-3">
            <label className="space-y-1 text-sm font-medium">Class name<Input name="name" placeholder="e.g. Form 1A, Form 3 Science" required /></label>
            <label className="space-y-1 text-sm font-medium">Grade/Form level
              <select value={gradeLevel} onChange={(event) => setGradeLevel(event.target.value)} required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                <option value="">Select level</option>
                {gradeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            {gradeLevel === "Custom" ? <label className="space-y-1 text-sm font-medium">Custom grade/form<Input value={customGrade} onChange={(event) => setCustomGrade(event.target.value)} placeholder="e.g. Grade 7 Red" required /></label> : null}
            <label className="space-y-1 text-sm font-medium">Stream/section<Input name="stream" placeholder="e.g. A, Red, Section 1" /></label>
            <label className="space-y-1 text-sm font-medium">Capacity<Input name="capacity" type="number" min="1" placeholder="e.g. 35" defaultValue="35" required /></label>
            <label className="space-y-1 text-sm font-medium">Academic year
              <select name="academicYearId" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                <option value="">Select academic year</option>
                {years.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
              </select>
            </label>
            <div className="flex items-end"><Button disabled={saving || (gradeLevel === "Custom" && !customGrade.trim())}>{saving ? "Saving..." : "Create Class"}</Button></div>
          </form>
        </Card>
      ) : null}

      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
      {message ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}

      {!classes.length ? (
        <Card><p className="py-10 text-center text-sm text-slate-500">No classes found. Create your first class to begin.</p></Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {classes.map((schoolClass) => (
            <Card key={schoolClass.id} className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold">{schoolClass.name}</h3>
                  <p className="text-sm text-slate-500">{schoolClass.gradeLevel}{schoolClass.stream ? ` - ${schoolClass.stream}` : ""}</p>
                </div>
                <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-brand">{schoolClass.enrollment} students</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                <Metric label="Subjects" value={schoolClass.subjectCount} />
                <Metric label="Teachers" value={schoolClass.teacherCount} />
                <Metric label="Capacity" value={schoolClass.capacity} />
                <Metric label="Year" value={schoolClass.academicYear || "-"} />
              </div>
              <p className="text-sm"><span className="font-semibold">Class Teacher:</span> {schoolClass.classTeacher?.name || "Not assigned"}</p>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => deleteClass(schoolClass)} disabled={deletingId === schoolClass.id} className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50">
                  <Trash2 className="h-4 w-4" /> Delete
                </button>
                <Button onClick={() => openDetail(schoolClass.id)}><Eye className="h-4 w-4" /> View Class</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {detail ? (
        <Card className="space-y-4">
          <div className="flex flex-col gap-2 border-b border-slate-100 pb-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-bold">{detail.item.name}</h2>
              <p className="text-sm text-slate-500">{detail.item.gradeLevel}{detail.item.stream ? ` - ${detail.item.stream}` : ""}</p>
            </div>
            <button onClick={() => setDetail(null)} className="text-sm font-semibold text-slate-500">Close details</button>
          </div>
          <div className="flex gap-2 overflow-x-auto">
            {tabs.map((tab) => (
              <button key={tab} type="button" onClick={() => setActiveTab(tab)} className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold ${activeTab === tab ? "bg-brand text-white" : "bg-slate-100 text-slate-600"}`}>{tab}</button>
            ))}
          </div>
          {activeTab === "Overview" ? <Overview detail={detail} /> : null}
          {activeTab === "Students" ? <StudentsTab students={detail.students} /> : null}
          {activeTab === "Subjects" ? <SubjectsTab subjects={detail.subjects} /> : null}
          {activeTab === "Teachers" ? <TeachersTab teachers={detail.teachers} classTeacher={detail.classTeacher} /> : null}
          {activeTab === "Attendance Summary" ? <Summary title="Attendance Summary" rows={[["Records", detail.attendanceSummary.records], ["Present", detail.attendanceSummary.present], ["Attendance rate", detail.attendanceSummary.attendanceRate == null ? "-" : `${detail.attendanceSummary.attendanceRate}%`]]} /> : null}
          {activeTab === "Performance Summary" ? <Summary title="Performance Summary" rows={[["Average score", detail.performanceSummary.averageScore ?? "-"], ["Exam results", detail.performanceSummary.examResultCount], ["Final results", detail.performanceSummary.finalResultCount]]} /> : null}
        </Card>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 font-semibold">{value}</p></div>;
}

function Overview({ detail }: { detail: ClassDetail }) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      <Metric label="Academic year" value={detail.item.academicYear || "-"} />
      <Metric label="Capacity" value={detail.item.capacity} />
      <Metric label="Students" value={detail.item.studentCount} />
      <Metric label="Subjects" value={detail.item.subjectCount} />
      <Metric label="Teachers" value={detail.item.teacherCount} />
      <Metric label="Class teacher" value={detail.classTeacher?.name || "No class teacher assigned."} />
    </div>
  );
}

function StudentsTab({ students }: { students: ClassDetail["students"] }) {
  if (!students.length) return <p className="py-8 text-center text-sm text-slate-500">No students are registered under this class.</p>;
  return <Table headers={["Registration", "Name", "Gender", "Parent/Guardian", "Status"]} rows={students.map((student) => [student.registrationNumber, student.name, student.gender || "-", student.parent || "-", student.status])} />;
}

function SubjectsTab({ subjects }: { subjects: ClassDetail["subjects"] }) {
  if (!subjects.length) return <p className="py-8 text-center text-sm text-slate-500">No subjects are assigned to this class yet.</p>;
  return <Table headers={["Code", "Subject", "Type"]} rows={subjects.map((subject) => [subject.code, subject.name, subject.subjectType || "-"])} />;
}

function TeachersTab({ teachers, classTeacher }: { teachers: ClassDetail["teachers"]; classTeacher?: ClassDetail["classTeacher"] }) {
  return (
    <div className="space-y-4">
      <p className="rounded-md bg-slate-50 px-3 py-2 text-sm"><span className="font-semibold">Class Teacher:</span> {classTeacher?.name || "No class teacher assigned."}</p>
      {!teachers.length ? <p className="py-8 text-center text-sm text-slate-500">No teachers are assigned to this class yet.</p> : null}
      {teachers.length ? <Table headers={["Teacher", "Subject", "Department", "Email", "Phone"]} rows={teachers.map((teacher) => [teacher.teacherName, `${teacher.subjectCode} - ${teacher.subjectName}`, teacher.department || "-", teacher.email, teacher.phone || "-"])} /> : null}
    </div>
  );
}

function Summary({ title, rows }: { title: string; rows: [string, string | number][] }) {
  return <div><h3 className="font-semibold">{title}</h3><div className="mt-3 grid gap-3 md:grid-cols-3">{rows.map(([label, value]) => <Metric key={label} label={label} value={value} />)}</div></div>;
}

function Table({ headers, rows }: { headers: string[]; rows: (string | number)[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr>{headers.map((header) => <th key={header} className="px-3 py-3">{header}</th>)}</tr></thead>
        <tbody className="divide-y divide-slate-100">{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex} className="px-3 py-3">{cell}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}
