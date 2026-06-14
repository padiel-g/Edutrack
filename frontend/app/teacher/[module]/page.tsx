import { ModulePage } from "@/components/layout/PageTemplate";

const titles: Record<string, string> = {
  "my-subjects": "My Subjects",
  attendance: "Attendance",
  "results-upload": "Results Upload",
  "continuous-assessment": "Continuous Assessment",
  assignments: "Assignments",
  submissions: "Submissions",
  "learning-materials": "Learning Materials",
  "class-performance": "Class Performance",
  "teacher-comments": "Teacher Comments"
};

const resources: Record<string, string> = {
  "my-subjects": "subjects",
  attendance: "attendance",
  "results-upload": "exam-results",
  "continuous-assessment": "continuous-assessments",
  assignments: "assignments",
  submissions: "submissions",
  "learning-materials": "learning-materials",
  "class-performance": "final-results",
  "teacher-comments": "report-cards"
};

export default function Page({ params }: { params: { module: string } }) {
  const title = titles[params.module] ?? "Teacher Module";
  const resource = resources[params.module] ?? params.module;
  return <ModulePage title={title} resource={resource} description="Work with assigned learners, classes, subjects, submissions, performance, and comments." />;
}
