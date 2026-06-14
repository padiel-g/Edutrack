"use client";

import { Download, Save, Search, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { api, apiDownload } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Option = { id: number; name: string; isCurrent?: boolean; academicYearId?: number };
type StudentOption = { id: number; registrationNumber: string; name: string };
type ClassOption = { id: number; name: string; isClassTeacher: boolean; subjects: Option[]; students: StudentOption[] };
type Result = {
  id: number;
  studentId: number;
  subject: { id: number; name: string; code: string };
  caMark: number;
  examMark: number;
  finalMark: number;
  effortGrade: string;
};
type Report = {
  id: number;
  student: { id: number; registrationNumber: string; name: string; gradeForm?: string; class?: string; classStream?: string };
  term: string;
  academicYear: string;
  classTeacher?: string;
  teacherComment?: string;
  overallAchievement?: string;
  attitudeToLearning?: string;
  behaviour?: string;
  attendance?: string;
  attendanceRate?: number;
  targets: string[];
  adminComment?: string;
  approvedBy?: string;
  approvedAt?: string;
  status: string;
  results: Result[];
  downloadUrl: string;
};
type OptionsResponse = {
  classes: ClassOption[];
  academicYears: Option[];
  terms: Option[];
  effortGrades: string[];
  summaryGrades: string[];
};

function Select({ value, onChange, children, disabled = false }: { value: string; onChange: (value: string) => void; children: React.ReactNode; disabled?: boolean }) {
  return <select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled} className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm disabled:bg-slate-100">{children}</select>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="space-y-1 text-sm font-medium"><span>{label}</span>{children}</label>;
}

function Notice({ error, success }: { error: string; success: string }) {
  return <>{error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}{success ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</p> : null}</>;
}

function useReportOptions() {
  const [options, setOptions] = useState<OptionsResponse>({ classes: [], academicYears: [], terms: [], effortGrades: [], summaryGrades: [] });
  const [error, setError] = useState("");
  useEffect(() => { api<OptionsResponse>("/teacher/report-options").then(setOptions).catch((err) => setError(err instanceof Error ? err.message : "Unable to load report options")); }, []);
  return { options, error };
}

export function TeacherResultEntry() {
  const { options, error: optionsError } = useReportOptions();
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [yearId, setYearId] = useState("");
  const [termId, setTermId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [caMark, setCaMark] = useState("");
  const [examMark, setExamMark] = useState("");
  const [finalMark, setFinalMark] = useState("");
  const [effortGrade, setEffortGrade] = useState("");
  const [saved, setSaved] = useState<Record<number, Result>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const selectedClass = options.classes.find((item) => String(item.id) === classId);
  const terms = options.terms.filter((item) => !yearId || item.academicYearId === Number(yearId));

  useEffect(() => {
    if (!classId || !subjectId || !yearId || !termId) return;
    api<{ items: Result[] }>(`/results/class/${classId}?subjectId=${subjectId}&academicYearId=${yearId}&termId=${termId}`)
      .then((data) => setSaved(Object.fromEntries(data.items.map((item) => [item.studentId, item]))))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load results"));
  }, [classId, subjectId, yearId, termId]);

  function chooseStudent(value: string) {
    setStudentId(value);
    const existing = saved[Number(value)];
    setCaMark(existing ? String(existing.caMark) : "");
    setExamMark(existing ? String(existing.examMark) : "");
    setFinalMark(existing ? String(existing.finalMark) : "");
    setEffortGrade(existing?.effortGrade ?? "");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(""); setSuccess("");
    try {
      const existing = saved[Number(studentId)];
      const result = await api<{ message: string; item: Result }>(existing ? `/results/${existing.id}` : "/results", {
        method: existing ? "PUT" : "POST",
        body: JSON.stringify({ studentId: Number(studentId), subjectId: Number(subjectId), academicYearId: Number(yearId), termId: Number(termId), caMark: Number(caMark), examMark: Number(examMark), finalMark: Number(finalMark), effortGrade }),
      });
      setSaved((current) => ({ ...current, [Number(studentId)]: result.item }));
      setSuccess(result.message);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save result"); }
  }

  return <div className="space-y-5">
    <Card className="space-y-4">
      <div><h2 className="text-lg font-semibold">Subject Result Entry</h2><p className="text-sm text-slate-500">Only classes and subjects assigned to you are available.</p></div>
      <Notice error={optionsError || error} success={success} />
      {!options.academicYears.length || !options.terms.length ? <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">An Admin must configure an Academic Year and Term before results can be entered.</p> : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Academic Year"><Select value={yearId} onChange={(value) => { setYearId(value); setTermId(""); }}><option value="">Select year</option>{options.academicYears.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field label="Term"><Select value={termId} onChange={setTermId} disabled={!yearId}><option value="">Select term</option>{terms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field label="Class / Form"><Select value={classId} onChange={(value) => { setClassId(value); setSubjectId(""); setStudentId(""); }}><option value="">Select class</option>{options.classes.filter((item) => item.subjects.length).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field label="Subject"><Select value={subjectId} onChange={setSubjectId} disabled={!classId}><option value="">Select subject</option>{selectedClass?.subjects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
      </div>
      <Field label="Student"><Select value={studentId} onChange={chooseStudent} disabled={!subjectId}><option value="">Search or select student</option>{selectedClass?.students.map((item) => <option key={item.id} value={item.id}>{item.registrationNumber} - {item.name}{saved[item.id] ? " (Saved)" : ""}</option>)}</Select></Field>
      {studentId ? <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Field label="CA Mark"><Input type="number" min="0" max="100" step="0.01" value={caMark} onChange={(e) => setCaMark(e.target.value)} required /></Field>
        <Field label="Exam Mark"><Input type="number" min="0" max="100" step="0.01" value={examMark} onChange={(e) => setExamMark(e.target.value)} required /></Field>
        <Field label="Final Mark (%)"><Input type="number" min="0" max="100" step="0.01" value={finalMark} onChange={(e) => setFinalMark(e.target.value)} required /></Field>
        <Field label="Effort"><Select value={effortGrade} onChange={setEffortGrade}><option value="">Select effort</option>{options.effortGrades.map((item) => <option key={item}>{item}</option>)}</Select></Field>
        <Button className="self-end"><Save className="h-4 w-4" />Save Marks</Button>
      </form> : null}
    </Card>
  </div>;
}

export function ClassTeacherReports() {
  const { options, error: optionsError } = useReportOptions();
  const classes = options.classes.filter((item) => item.isClassTeacher);
  const [classId, setClassId] = useState("");
  const [yearId, setYearId] = useState("");
  const [termId, setTermId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [compiled, setCompiled] = useState<{ results: Result[]; attendanceRate: number; report?: Report | null } | null>(null);
  const [teacherComment, setTeacherComment] = useState("");
  const [overallAchievement, setOverallAchievement] = useState("");
  const [attitudeToLearning, setAttitudeToLearning] = useState("");
  const [behaviour, setBehaviour] = useState("");
  const [attendance, setAttendance] = useState("");
  const [targets, setTargets] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const selectedClass = classes.find((item) => String(item.id) === classId);
  const terms = options.terms.filter((item) => !yearId || item.academicYearId === Number(yearId));

  async function loadReport() {
    setError(""); setSuccess("");
    try {
      const data = await api<{ results: Result[]; attendanceRate: number; report?: Report | null }>(`/reports/student/${studentId}?academicYearId=${yearId}&termId=${termId}`);
      setCompiled(data);
      const report = data.report;
      setTeacherComment(report?.teacherComment ?? "");
      setOverallAchievement(report?.overallAchievement ?? "");
      setAttitudeToLearning(report?.attitudeToLearning ?? "");
      setBehaviour(report?.behaviour ?? "");
      setAttendance(report?.attendance ?? (data.attendanceRate >= 90 ? "Excellent" : data.attendanceRate >= 75 ? "Good" : "Needs Improvement"));
      setTargets(report?.targets.join("\n") ?? "");
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to compile report"); }
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setSuccess("");
    try {
      const data = await api<{ message: string; report: Report }>("/reports/complete", {
        method: "POST",
        body: JSON.stringify({ studentId: Number(studentId), academicYearId: Number(yearId), termId: Number(termId), teacherComment, overallAchievement, attitudeToLearning, behaviour, attendance, targets: targets.split("\n") }),
      });
      setCompiled((current) => current ? { ...current, report: data.report } : current);
      setSuccess(data.message);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to submit report"); }
  }

  return <div className="space-y-5">
    <Card className="space-y-4">
      <div><h2 className="text-lg font-semibold">Complete Student Report</h2><p className="text-sm text-slate-500">Only classes where you are the assigned Class Teacher are shown.</p></div>
      <Notice error={optionsError || error} success={success} />
      {!classes.length ? <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">You are not assigned as a Class Teacher.</p> : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Academic Year"><Select value={yearId} onChange={(v) => { setYearId(v); setTermId(""); }}><option value="">Select year</option>{options.academicYears.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field label="Term"><Select value={termId} onChange={setTermId} disabled={!yearId}><option value="">Select term</option>{terms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field label="Class"><Select value={classId} onChange={(v) => { setClassId(v); setStudentId(""); setCompiled(null); }}><option value="">Select class</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field label="Student"><Select value={studentId} onChange={(v) => { setStudentId(v); setCompiled(null); }} disabled={!classId}><option value="">Select student</option>{selectedClass?.students.map((item) => <option key={item.id} value={item.id}>{item.registrationNumber} - {item.name}</option>)}</Select></Field>
      </div>
      <Button type="button" onClick={loadReport} disabled={!studentId || !termId || !yearId}><Search className="h-4 w-4" />Compile Report</Button>
    </Card>
    {compiled ? <form onSubmit={submit} className="space-y-5">
      <Card><h3 className="mb-3 font-semibold">Submitted Subject Results</h3><ResultsTable results={compiled.results} /><p className="mt-3 text-sm text-slate-500">Calculated attendance rate: {compiled.attendanceRate}%</p></Card>
      <Card className="grid gap-4 lg:grid-cols-2">
        <Field label="Class Teacher Comment"><textarea value={teacherComment} onChange={(e) => setTeacherComment(e.target.value)} required rows={7} className="w-full rounded-md border border-slate-300 p-3 text-sm" /></Field>
        <div className="grid gap-3 sm:grid-cols-2">
          {[["Overall Achievement", overallAchievement, setOverallAchievement], ["Attitude to Learning", attitudeToLearning, setAttitudeToLearning], ["Behaviour", behaviour, setBehaviour], ["Attendance", attendance, setAttendance]].map(([label, value, setter]) => <Field key={label as string} label={label as string}><Select value={value as string} onChange={setter as (value: string) => void}><option value="">Select</option>{options.summaryGrades.map((item) => <option key={item}>{item}</option>)}</Select></Field>)}
        </div>
        <Field label="Next Term / Next Year Targets (one per line)"><textarea value={targets} onChange={(e) => setTargets(e.target.value)} required rows={6} className="w-full rounded-md border border-slate-300 p-3 text-sm" /></Field>
        <div className="flex items-end"><Button className="w-full"><Send className="h-4 w-4" />Save & Submit for Approval</Button></div>
      </Card>
    </form> : null}
  </div>;
}

export function AdminReportApproval() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selected, setSelected] = useState<Report | null>(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const load = () => api<{ items: Report[] }>("/reports/pending").then((data) => { setReports(data.items); if (selected) setSelected(data.items.find((item) => item.id === selected.id) ?? null); }).catch((err) => setError(err instanceof Error ? err.message : "Unable to load reports"));
  useEffect(() => {
    void load();
  }, []);
  async function action(name: "approve" | "return" | "reject") {
    if (!selected) return;
    setError(""); setSuccess("");
    try {
      const data = await api<{ message: string; report: Report }>(`/reports/${name}`, { method: "POST", body: JSON.stringify({ reportId: selected.id, comment }) });
      setSelected(data.report); setSuccess(data.message); setComment(""); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to update report"); }
  }
  return <div className="grid gap-5 xl:grid-cols-[320px_1fr]">
    <Card><h2 className="font-semibold">Reports for Review</h2><div className="mt-3 space-y-2">{reports.length ? reports.map((report) => <button key={report.id} onClick={() => setSelected(report)} className={`w-full rounded-md border p-3 text-left text-sm ${selected?.id === report.id ? "border-brand bg-teal-50" : "border-slate-200"}`}><span className="block font-semibold">{report.student.name}</span><span className="text-slate-500">{report.term} - {report.academicYear}</span><span className="mt-1 block text-xs text-brand">{report.status}</span></button>) : <p className="text-sm text-slate-500">No reports submitted.</p>}</div></Card>
    <div className="space-y-4"><Notice error={error} success={success} />{selected ? <><ReportPreview report={selected} /><Card className="space-y-3"><Field label="Admin comment"><textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} className="w-full rounded-md border border-slate-300 p-3 text-sm" /></Field><div className="flex flex-wrap gap-2"><Button onClick={() => action("approve")}>Approve & Publish</Button><Button className="bg-amber-600 hover:bg-amber-700" onClick={() => action("return")}>Return for Corrections</Button><Button className="bg-red-600 hover:bg-red-700" onClick={() => action("reject")}>Reject</Button></div></Card></> : <Card><p className="text-sm text-slate-500">Select a report to review.</p></Card>}</div>
  </div>;
}

export function ParentReportCards() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api<{ items: Report[] }>("/parent/reports").then((data) => { setReports(data.items); setSelectedId(data.items[0] ? String(data.items[0].id) : ""); }).catch((err) => setError(err instanceof Error ? err.message : "Unable to load reports")); }, []);
  const selected = reports.find((item) => String(item.id) === selectedId);
  return <div className="space-y-5"><Notice error={error} success="" /><Card><Field label="Published Report"><Select value={selectedId} onChange={setSelectedId}><option value="">Select report</option>{reports.map((report) => <option key={report.id} value={report.id}>{report.term} - {report.academicYear}</option>)}</Select></Field></Card>{selected ? <ReportPreview report={selected} downloadable /> : <Card><p className="text-sm text-slate-500">No published report cards are available yet.</p></Card>}</div>;
}

async function downloadReport(report: Report) {
  const blob = await apiDownload(report.downloadUrl);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${report.student.registrationNumber}-${report.term}-report.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}

function ResultsTable({ results }: { results: Result[] }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-left text-sm"><thead className="bg-[#08285c] text-white"><tr><th className="p-3">Subject</th><th className="p-3 text-center">Result</th><th className="p-3 text-center">Effort</th></tr></thead><tbody className="divide-y">{results.map((result) => <tr key={result.id}><td className="p-3">{result.subject.name}</td><td className="p-3 text-center font-bold">{result.finalMark}%</td><td className="p-3 text-center">{result.effortGrade}</td></tr>)}</tbody></table></div>;
}

export function ReportPreview({ report, downloadable = false }: { report: Report; downloadable?: boolean }) {
  return <Card className="mx-auto max-w-5xl border-slate-300">
    <div className="border-b-2 border-[#08285c] pb-4 text-center"><h2 className="text-2xl font-bold text-[#08285c]">{report.student.name} {report.term} Report</h2><p className="text-sm text-slate-500">EduTrack School</p></div>
    <div className="grid gap-2 py-4 text-sm sm:grid-cols-2"><p><b>Registration:</b> {report.student.registrationNumber}</p><p><b>Form / Class:</b> {[report.student.class || report.student.gradeForm, report.student.classStream].filter(Boolean).join(" - ")}</p><p><b>Academic Year:</b> {report.academicYear}</p><p><b>Class Teacher:</b> {report.classTeacher || "-"}</p></div>
    <ResultsTable results={report.results} />
    <div className="mt-5 grid gap-4 lg:grid-cols-2">
      <section className="border border-slate-300"><h3 className="bg-[#08285c] p-2 text-center font-semibold text-white">CLASS TEACHER COMMENT</h3><p className="p-4 whitespace-pre-line text-sm">{report.teacherComment}</p></section>
      <section className="border border-slate-300"><h3 className="bg-[#08285c] p-2 text-center font-semibold text-white">SUMMARY</h3><dl className="divide-y text-sm">{[["Overall Achievement", report.overallAchievement], ["Attitude to Learning", report.attitudeToLearning], ["Behaviour", report.behaviour], ["Attendance", report.attendance]].map(([label, value]) => <div key={label} className="grid grid-cols-2 p-2"><dt className="font-semibold">{label}</dt><dd>{value}</dd></div>)}</dl></section>
    </div>
    <section className="mt-4 border border-slate-300"><h3 className="bg-[#08285c] p-2 text-center font-semibold text-white">NEXT TERM / NEXT YEAR TARGETS</h3><ul className="list-disc space-y-1 p-4 pl-8 text-sm">{report.targets.map((target) => <li key={target}>{target}</li>)}</ul></section>
    <div className="mt-4 grid gap-2 border-t pt-4 text-sm sm:grid-cols-2"><p><b>Status:</b> {report.status}</p><p><b>Approved By:</b> {report.approvedBy || "-"}</p>{report.adminComment ? <p className="sm:col-span-2"><b>Admin Comment:</b> {report.adminComment}</p> : null}</div>
    {(downloadable || ["Published", "Approved"].includes(report.status)) ? <Button className="mt-4" onClick={() => downloadReport(report)}><Download className="h-4 w-4" />Download / Print PDF</Button> : null}
  </Card>;
}
