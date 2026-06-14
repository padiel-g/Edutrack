"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AnnouncementFeed } from "@/components/announcements/AnnouncementFeed";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { getUser } from "@/lib/auth";

type ParentSummary = {
  student: {
    registrationNumber: string;
    name: string;
    form?: string;
    class?: string;
    stream?: string;
    currentBalance: number;
    totalPaid: number;
    status: string;
  };
  payments: {
    id: number;
    amount: number;
    method: string;
    paidAt: string;
    receipt?: { receiptNumber: string } | null;
  }[];
};

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export function ParentDashboard() {
  const [summary, setSummary] = useState<ParentSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const studentId = getUser()?.id;
    if (!studentId) return;
    api<ParentSummary>(`/parents/children/${studentId}/payments`)
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load your child's information"));
  }, []);

  const student = summary?.student;
  const latestPayment = summary?.payments[0];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Parent Dashboard</h1>
        <p className="text-slate-500">Your child&apos;s school information and latest updates.</p>
      </div>

      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <p className="text-sm text-slate-500">Student</p>
          <p className="mt-2 text-xl font-bold">{student?.name ?? "Loading..."}</p>
          <p className="mt-1 text-sm text-slate-600">{student?.registrationNumber ?? ""}</p>
          <p className="mt-1 text-sm text-brand">
            {[student?.form || student?.class, student?.stream].filter(Boolean).join(" - ")}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Current Fee Balance</p>
          <p className="mt-2 text-2xl font-bold">{student ? money(Math.max(student.currentBalance, 0)) : "..."}</p>
          <p className="mt-1 text-sm text-brand">{student?.status ?? "Loading"}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Latest Payment</p>
          <p className="mt-2 text-2xl font-bold">{latestPayment ? money(latestPayment.amount) : "No payment yet"}</p>
          {latestPayment ? (
            <p className="mt-1 text-sm text-slate-600">
              {new Date(latestPayment.paidAt).toLocaleDateString()} via {latestPayment.method}
            </p>
          ) : null}
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Link href="/parent/child-results" className="rounded-lg border border-slate-200 bg-white p-4 font-semibold text-brand shadow-soft">View Results</Link>
        <Link href="/parent/child-attendance" className="rounded-lg border border-slate-200 bg-white p-4 font-semibold text-brand shadow-soft">View Attendance</Link>
        <Link href="/parent/child-fees" className="rounded-lg border border-slate-200 bg-white p-4 font-semibold text-brand shadow-soft">Fees & Payments</Link>
      </div>

      <AnnouncementFeed showPopup />
    </div>
  );
}
