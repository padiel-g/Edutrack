import { notFound } from "next/navigation";
import { ModulePage } from "@/components/layout/PageTemplate";

const titles: Record<string, string> = {
  "my-results": "My Results",
  "my-attendance": "My Attendance",
  "my-assignments": "My Assignments",
  "learning-materials": "Learning Materials",
  timetable: "Timetable",
  "fee-balance": "Fee Balance",
  announcements: "Announcements"
};

const resources: Record<string, string> = {
  "my-results": "exam-results",
  "my-attendance": "attendance",
  "my-assignments": "assignments",
  "learning-materials": "learning-materials",
  timetable: "timetables",
  "fee-balance": "student-fee-accounts",
  announcements: "announcements"
};

export default function Page({ params }: { params: { module: string } }) {
  if (params.module === "report-cards") notFound();
  const title = titles[params.module] ?? "Student Module";
  const resource = resources[params.module] ?? params.module;
  return <ModulePage title={title} resource={resource} description="View academic records, attendance, assignments, fee status, materials, and downloadable reports." />;
}
