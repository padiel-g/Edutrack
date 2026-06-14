import { ModulePage } from "@/components/layout/PageTemplate";
import { AdminFeesOverview } from "@/components/finance/FinanceWorkflow";

const titles: Record<string, string> = {
  students: "Students",
  teachers: "Teachers",
  parents: "Parents",
  classes: "Classes",
  subjects: "Subjects",
  "academic-years": "Academic Years",
  terms: "Terms",
  timetable: "Timetable",
  announcements: "Announcements",
  reports: "Reports",
  "users-and-roles": "Users and Roles",
  "audit-logs": "Audit Logs",
  settings: "School Settings",
  "fees-overview": "Fees Overview"
};

const resources: Record<string, string> = {
  students: "students",
  teachers: "teachers",
  parents: "parents",
  classes: "classes",
  subjects: "subjects",
  "academic-years": "academic-years",
  terms: "terms",
  timetable: "timetables",
  announcements: "announcements",
  reports: "report-cards",
  "users-and-roles": "users",
  "audit-logs": "audit-logs",
  settings: "settings"
};

export default function Page({ params }: { params: { module: string } }) {
  if (params.module === "fees-overview") {
    return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Fees Overview</h1><p className="text-slate-500">Monitor student fees, payments, balances, and account status.</p></div><AdminFeesOverview /></div>;
  }
  const title = titles[params.module] ?? "Admin Module";
  const resource = resources[params.module] ?? params.module;
  return <ModulePage title={title} resource={resource} description="Manage records, permissions, relationships, exports, and operational workflows." />;
}
