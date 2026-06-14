"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FinancePie } from "@/components/charts/AnalyticsCharts";
import { DataTable } from "@/components/tables/DataTable";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

type FinanceDashboard = {
  totals: {
    totalInvoiced: number;
    totalPaid: number;
    outstandingBalance: number;
    paidStudents: number;
    unpaidStudents: number;
    partiallyPaidStudents: number;
    overdueInvoices: number;
    todaysCollections: number;
  };
  monthlyCollections: { month: string; amount: number }[];
  paidVsUnpaid: { name: string; value: number }[];
  paymentMethods: { name: string; value: number }[];
  outstandingByClass: { className: string; amount: number }[];
};

const emptyFinance: FinanceDashboard = {
  totals: {
    totalInvoiced: 0,
    totalPaid: 0,
    outstandingBalance: 0,
    paidStudents: 0,
    unpaidStudents: 0,
    partiallyPaidStudents: 0,
    overdueInvoices: 0,
    todaysCollections: 0
  },
  monthlyCollections: [],
  paidVsUnpaid: [],
  paymentMethods: [],
  outstandingByClass: []
};

const colors = ["#0f766e", "#e85d45", "#d59e1f", "#172033"];

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export function AccountsDashboard() {
  const [data, setData] = useState<FinanceDashboard>(emptyFinance);
  const [error, setError] = useState("");

  useEffect(() => {
    api<FinanceDashboard>("/finance/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load finance dashboard"));
  }, []);

  const stats = [
    ["Total invoiced", money(data.totals.totalInvoiced), "From invoices"],
    ["Total paid", money(data.totals.totalPaid), "From payments"],
    ["Outstanding", money(data.totals.outstandingBalance), `${data.totals.overdueInvoices} overdue`],
    ["Today collected", money(data.totals.todaysCollections), "From today's payments"]
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Accounts Officer Dashboard</h1>
        <p className="text-slate-500">Invoices, receipts, balances, collections, reminders, and finance reporting from PostgreSQL.</p>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(([label, value, meta]) => (
          <Card key={label}>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold">{value}</p>
            <p className="mt-1 text-xs text-brand">{meta}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <DataTable title="Recent Payments" resource="payments" action="Record payment" />
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Fee Collection Rate</h2>
          <FinancePie paid={data.totals.totalPaid} outstanding={data.totals.outstandingBalance} />
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <FinanceBar title="Monthly Collections" data={data.monthlyCollections.map((item) => ({ name: item.month, value: item.amount }))} />
        <FinanceBar title="Outstanding Balances by Class" data={data.outstandingByClass.map((item) => ({ name: item.className, value: item.amount }))} />
        <FinancePieCard title="Paid vs Unpaid Students" data={data.paidVsUnpaid} />
        <FinancePieCard title="Payment Methods" data={data.paymentMethods} />
      </div>
    </div>
  );
}

function FinanceBar({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {data.length ? (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      ) : <div className="grid h-[240px] place-items-center text-sm text-slate-500">No records available.</div>}
    </Card>
  );
}

function FinancePieCard({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {data.some((entry) => entry.value > 0) ? (
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" outerRadius={86} label>
              {data.map((entry, index) => <Cell key={entry.name} fill={colors[index % colors.length]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      ) : <div className="grid h-[240px] place-items-center text-sm text-slate-500">No records available.</div>}
    </Card>
  );
}
