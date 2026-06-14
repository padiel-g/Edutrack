import { notFound } from "next/navigation";
import { ModulePage } from "@/components/layout/PageTemplate";
import { StudentFeeAccountsByClass } from "@/components/finance/StudentFeeAccountsByClass";
import { PaymentHistory, RecordPaymentForm } from "@/components/finance/FinanceWorkflow";

const titles: Record<string, string> = {
  "student-fee-accounts": "Student Fee Accounts",
  invoices: "Invoices",
  payments: "Payments",
  "record-payment": "Record Payment",
  "paid-students": "Paid Students",
  "unpaid-students": "Unpaid Students",
  "overdue-balances": "Overdue Balances",
  "fee-reminders": "Fee Reminders",
  "finance-reports": "Finance Reports",
  settings: "Accounts Settings"
};

const resources: Record<string, string> = {
  "student-fee-accounts": "student-fee-accounts",
  invoices: "invoices",
  payments: "payments",
  "record-payment": "payments",
  "paid-students": "student-fee-accounts",
  "unpaid-students": "student-fee-accounts",
  "overdue-balances": "invoices",
  "fee-reminders": "fee-reminders",
  "finance-reports": "report-cards",
  settings: "settings"
};

export default function Page({ params }: { params: { module: string } }) {
  if (["create-invoice", "receipts", "partially-paid-students"].includes(params.module)) notFound();
  const title = titles[params.module] ?? "Accounts Module";
  const resource = resources[params.module] ?? params.module;
  if (params.module === "student-fee-accounts") {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="text-slate-500">Select a class to view its student fee accounts and balances.</p>
        </div>
        <StudentFeeAccountsByClass />
      </div>
    );
  }
  if (params.module === "record-payment") {
    return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Record Payment</h1><p className="text-slate-500">Search a student, post a fee payment, and generate an official receipt.</p></div><RecordPaymentForm /></div>;
  }
  if (params.module === "payments") {
    return <div className="space-y-5"><div><h1 className="text-2xl font-bold">{title}</h1><p className="text-slate-500">View recorded payments and download generated receipts.</p></div><PaymentHistory /></div>;
  }
  return <ModulePage title={title} resource={resource} description="Manage invoices, payments, receipts, reminders, revenue analytics, and finance exports." />;
}
