import { AdminReportApproval } from "@/components/reports/ReportCardWorkflow";

export default function Page() {
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Report Cards</h1><p className="text-slate-500">Review, return, reject, approve, and publish student reports.</p></div><AdminReportApproval /></div>;
}
