"use client";

import { useEffect, useState } from "react";
import { FinancePie, PerformanceChart } from "@/components/charts/AnalyticsCharts";
import { DataTable } from "@/components/tables/DataTable";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { AnnouncementFeed } from "@/components/announcements/AnnouncementFeed";

type Analytics = {
  totals: { students: number; teachers: number; parents: number; classes: number };
  attendance: { presentRate: number; absenceRate: number };
  finance: { totalInvoiced: number; totalPaid: number; outstandingBalance: number; collectionRate: number };
  recentAnnouncements: { title: string; audience?: string }[];
  recentAuditLogs: { action: string; entity: string }[];
};

const emptyAnalytics: Analytics = {
  totals: { students: 0, teachers: 0, parents: 0, classes: 0 },
  attendance: { presentRate: 0, absenceRate: 0 },
  finance: { totalInvoiced: 0, totalPaid: 0, outstandingBalance: 0, collectionRate: 0 },
  recentAnnouncements: [],
  recentAuditLogs: []
};

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export function DashboardHome({ role }: { role: string }) {
  const [analytics, setAnalytics] = useState<Analytics>(emptyAnalytics);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    function loadAnalytics() {
      api<Analytics>("/dashboard/analytics")
      .then((data) => {
        if (active) setAnalytics(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Unable to load dashboard");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    }

    function refreshOnFocus() {
      if (document.visibilityState === "visible") loadAnalytics();
    }

    loadAnalytics();
    const interval = window.setInterval(loadAnalytics, 60000);
    window.addEventListener("focus", loadAnalytics);
    document.addEventListener("visibilitychange", refreshOnFocus);

    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", loadAnalytics);
      document.removeEventListener("visibilitychange", refreshOnFocus);
    };
  }, []);

  const cards = [
    ["Total students", analytics.totals.students, "Registered"],
    ["Teachers", analytics.totals.teachers, "In PostgreSQL"],
    ["Classes", analytics.totals.classes, "Configured"],
    ["Outstanding fees", money(analytics.finance.outstandingBalance), `${analytics.finance.collectionRate}% collected`]
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{role} Dashboard</h1>
        <p className="text-slate-500">Live operational overview from PostgreSQL.</p>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(([label, value, meta]) => (
          <Card key={label}>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold">{loading ? "..." : value}</p>
            <p className="mt-1 text-xs text-brand">{meta}</p>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Class and Subject Performance</h2>
          <PerformanceChart />
        </Card>
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Fee Collection</h2>
          <FinancePie paid={analytics.finance.totalPaid} outstanding={analytics.finance.outstandingBalance} />
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {role === "Teacher" || role === "Parent" ? <AnnouncementFeed showPopup /> : (
          <Card>
            <h3 className="font-semibold">Announcements</h3>
            {analytics.recentAnnouncements.length ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-600">
                {analytics.recentAnnouncements.map((item) => <li key={`${item.title}-${item.audience}`}>{item.title}</li>)}
              </ul>
            ) : <p className="mt-2 text-sm text-slate-500">No announcements found.</p>}
          </Card>
        )}
        <Card>
          <h3 className="font-semibold">Recent activity</h3>
          {analytics.recentAuditLogs.length ? (
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              {analytics.recentAuditLogs.map((item) => <li key={`${item.action}-${item.entity}`}>{item.action} ({item.entity})</li>)}
            </ul>
          ) : <p className="mt-2 text-sm text-slate-500">No activity found.</p>}
        </Card>
      </div>
    </div>
  );
}

export function ModulePage({ title, description, resource }: { title: string; description: string; resource: string }) {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-slate-500">{description}</p>
      </div>
      <DataTable title={title} resource={resource} />
    </div>
  );
}
