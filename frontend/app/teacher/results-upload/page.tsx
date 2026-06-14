import { TeacherResultEntry } from "@/components/reports/ReportCardWorkflow";

export default function Page() {
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Results Upload</h1><p className="text-slate-500">Enter marks for your assigned classes and subjects.</p></div><TeacherResultEntry /></div>;
}
