"use client";

import { ChevronLeft, ChevronRight, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type RecordItem = Record<string, unknown> & { id: number };

const resourceLabels: Record<string, string> = {
  teachers: "teachers",
  parents: "parents",
  classes: "classes",
  subjects: "subjects",
  announcements: "announcements",
  "report-cards": "reports",
  students: "students"
};

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return `${value.length}`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function columnsFor(items: RecordItem[]) {
  const hidden = new Set(["id", "passwordHash", "createdById", "updatedById"]);
  const keys = new Set<string>();
  items.forEach((item) => {
    Object.keys(item).forEach((key) => {
      if (!hidden.has(key)) keys.add(key);
    });
  });
  return Array.from(keys).slice(0, 5);
}

export function DataTable({ title, resource, action = "Add record" }: { title: string; resource: string; action?: string }) {
  const [items, setItems] = useState<RecordItem[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const perPage = 10;
  const readOnly = getUser()?.role === "Parent";

  const columns = useMemo(() => columnsFor(items), [items]);
  const totalPages = Math.max(Math.ceil(total / perPage), 1);

  async function load(nextPage = page) {
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams({ page: String(nextPage), perPage: String(perPage), search });
      const response = await api<{ items: RecordItem[]; total: number }>(`/${resource}?${query}`);
      setItems(response.items);
      setTotal(response.total ?? response.items.length);
      setPage(nextPage);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load records");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(1);
  }, [resource]);

  async function remove(id: number) {
    if (!confirm("Delete this record?")) return;
    await api(`/${resource}/${id}`, { method: "DELETE" });
    await load(page);
  }

  const emptyLabel = resourceLabels[resource] ?? "records";

  return (
    <Card className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-slate-500">Records are loaded from PostgreSQL.</p>
        </div>
        <Button disabled>{action}</Button>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_120px]">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search records" />
        </div>
        <Button onClick={() => load(1)} disabled={loading}>Search</Button>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {loading ? <p className="py-8 text-center text-sm text-slate-500">Loading records...</p> : null}
      {!loading && !items.length ? <p className="py-8 text-center text-sm text-slate-500">No {emptyLabel} found.</p> : null}
      {!loading && items.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                {columns.map((column) => <th key={column} className="px-3 py-3">{column}</th>)}
                {!readOnly ? <th className="px-3 py-3 text-right">Actions</th> : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.id}>
                  {columns.map((column) => <td key={column} className="px-3 py-3">{displayValue(item[column])}</td>)}
                  {!readOnly ? <td className="px-3 py-3 text-right">
                    <button onClick={() => remove(item.id)} className="rounded-md p-2 text-coral" aria-label="Delete">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td> : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1 || loading} onClick={() => load(page - 1)} className="rounded-md border border-slate-200 p-2 disabled:opacity-40" aria-label="Previous page"><ChevronLeft className="h-4 w-4" /></button>
          <button disabled={page >= totalPages || loading} onClick={() => load(page + 1)} className="rounded-md border border-slate-200 p-2 disabled:opacity-40" aria-label="Next page"><ChevronRight className="h-4 w-4" /></button>
        </div>
      </div>
    </Card>
  );
}
