"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Download, FileText, ReceiptText } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import type { Student } from "@/types/student";

type Profile = {
  student: Student;
  class?: { id: number; name: string };
  feeAccount?: { accountNumber: string; currentBalance: number };
  invoices: { id: number; invoiceNumber: string; amount: number; balance: number; status: string }[];
  payments: { id: number; paymentReference: string; amount: number; method: string }[];
};

export default function Page() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ profile: Profile }>(`/admin/students/${params.id}/profile`)
      .then((response) => setProfile(response.profile))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load profile"));
  }, [params.id]);

  if (error) return <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>;
  if (!profile) return <p className="text-sm text-slate-500">Loading student profile...</p>;

  const student = profile.student;
  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">{student.name}</h1>
          <p className="text-slate-500">Registration No. <span className="font-semibold text-ink">{student.registrationNumber}</span></p>
        </div>
        <div className="flex gap-2">
          <Button><FileText className="h-4 w-4" /> Report card</Button>
          <Button className="bg-ink hover:bg-slate-800"><Download className="h-4 w-4" /> Export profile</Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><p className="text-sm text-slate-500">Grade / Form</p><p className="mt-2 text-xl font-bold">{student.gradeForm ?? "Unassigned"}</p></Card>
        <Card><p className="text-sm text-slate-500">Class / Stream</p><p className="mt-2 text-xl font-bold">{student.classStream ?? student.class ?? "Unassigned"}</p></Card>
        <Card><p className="text-sm text-slate-500"># Subjects</p><p className="mt-2 text-xl font-bold">{student.numberOfSubjects ?? student.subjects?.length ?? 0}</p></Card>
        <Card><p className="text-sm text-slate-500">Status</p><p className="mt-2 text-xl font-bold capitalize">{student.status}</p></Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card><p className="text-sm text-slate-500">Fee Account</p><p className="mt-2 text-xl font-bold">{profile.feeAccount?.accountNumber ?? "Pending"}</p></Card>
        <Card><p className="text-sm text-slate-500">Balance</p><p className="mt-2 text-xl font-bold">${profile.feeAccount?.currentBalance ?? 0}</p></Card>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Student Details</h2>
          <dl className="grid gap-3 text-sm md:grid-cols-2">
            <Info label="Registration No." value={student.registrationNumber} />
            <Info label="Gender" value={student.gender} />
            <Info label="Date of birth" value={student.dateOfBirth} />
            <Info label="Birth certificate" value={student.birthCertificateNumber} />
            <Info label="National ID" value={student.nationalId} />
            <Info label="Email" value={student.email} />
            <Info label="Phone" value={student.phone} />
            <Info label="Address" value={student.address} />
          </dl>
        </Card>
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Academic Details</h2>
          <dl className="grid gap-3 text-sm md:grid-cols-2">
            <Info label="Registration No." value={student.registrationNumber} />
            <Info label="Grade / Form" value={student.gradeForm} />
            <Info label="Class / Stream" value={student.classStream} />
            <Info label="Number of subjects" value={student.numberOfSubjects != null ? String(student.numberOfSubjects) : null} />
          </dl>
          <div className="mt-4">
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Registered subjects</p>
            {student.subjects?.length ? (
              <ul className="flex flex-wrap gap-2">
                {student.subjects.map((subject) => (
                  <li
                    key={subject.id}
                    className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-medium text-brand"
                  >
                    {subject.name}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No subjects registered yet.</p>
            )}
          </div>
        </Card>
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Invoices and Receipts</h2>
          <div className="space-y-3">
            {profile.invoices.map((invoice) => (
              <div key={invoice.id} className="flex items-center justify-between rounded-md border border-slate-200 p-3 text-sm">
                <div>
                  <p className="font-semibold">{invoice.invoiceNumber}</p>
                  <p className="text-slate-500">{student.registrationNumber} · {invoice.status}</p>
                </div>
                <p className="font-semibold">${invoice.balance}</p>
              </div>
            ))}
            {profile.payments.map((payment) => (
              <div key={payment.id} className="flex items-center justify-between rounded-md bg-slate-50 p-3 text-sm">
                <p><ReceiptText className="mr-2 inline h-4 w-4" />{payment.paymentReference}</p>
                <p className="font-semibold">${payment.amount}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-semibold">{value || "-"}</dd>
    </div>
  );
}
