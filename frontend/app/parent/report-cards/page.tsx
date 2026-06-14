import { ParentReportCards } from "@/components/reports/ReportCardWorkflow";

export default function Page() {
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Report Cards</h1><p className="text-slate-500">View and download approved reports for your child.</p></div><ParentReportCards /></div>;
}
