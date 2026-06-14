"use client";

import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function PerformanceChart({ data = [] }: { data?: { name: string; pass: number; fail: number }[] }) {
  if (!data.length) {
    return <div className="grid h-[260px] place-items-center text-sm text-slate-500">No performance records available.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="pass" fill="#0f766e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="fail" fill="#e85d45" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function FinancePie({ paid = 0, outstanding = 0 }: { paid?: number; outstanding?: number }) {
  const data = [
    { name: "Paid", value: paid, color: "#0f766e" },
    { name: "Outstanding", value: outstanding, color: "#d59e1f" }
  ];
  if (!paid && !outstanding) {
    return <div className="grid h-[220px] place-items-center text-sm text-slate-500">No finance records available.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" outerRadius={84} label>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}
