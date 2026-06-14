import { ModulePage } from "@/components/layout/PageTemplate";
import { PaymentHistory } from "@/components/finance/FinanceWorkflow";

const titles: Record<string, string> = {
  "my-children": "My Children",
  "child-results": "Child Results",
  "child-attendance": "Child Attendance",
  "child-fees": "Child Fees",
  "payment-history": "Payment History",
  "report-cards": "Report Cards",
  "teacher-comments": "Teacher Comments",
  announcements: "Announcements",
  notifications: "Notifications"
};

const resources: Record<string, string> = {
  "my-children": "students",
  "child-results": "exam-results",
  "child-attendance": "attendance",
  "child-fees": "student-fee-accounts",
  "payment-history": "payments",
  "report-cards": "report-cards",
  "teacher-comments": "report-cards",
  announcements: "announcements",
  notifications: "notifications"
};

export default function Page({ params }: { params: { module: string } }) {
  if (params.module === "child-fees" || params.module === "payment-history") {
    return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Fees & Payments</h1><p className="text-slate-500">View the latest balance, payment history, and receipts for your child.</p></div><PaymentHistory parent /></div>;
  }
  const title = titles[params.module] ?? "Parent Module";
  const resource = resources[params.module] ?? params.module;
  return <ModulePage title={title} resource={resource} description="Information for the student registration number used to sign in." />;
}
