import { ClassTeacherReports } from "@/components/reports/ReportCardWorkflow";

export default function Page() {
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Complete Reports</h1><p className="text-slate-500">Compile subject results and submit student reports for approval.</p></div><ClassTeacherReports /></div>;
}
