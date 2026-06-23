"use client";

import { Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type ParentRecord = {
  id: number;
  name: string;
  children?: string[];
};

export function AdminParentsManager() {
  const [parents, setParents] = useState<ParentRecord[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const filteredParents = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return parents;
    return parents.filter((parent) => {
      const children = (parent.children ?? []).join(" ").toLowerCase();
      return parent.name.toLowerCase().includes(term) || children.includes(term);
    });
  }, [parents, search]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const response = await api<{ items: ParentRecord[] }>("/parents?perPage=100");
      setParents(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load parents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(parent: ParentRecord) {
    if (!confirm(`Delete ${parent.name}? Linked students will stay registered, but this parent record will be removed.`)) return;
    setError("");
    try {
      await api(`/parents/${parent.id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete parent");
    }
  }

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Parent Records</h2>
        <p className="text-sm text-slate-500">Delete guardian records without deleting linked students.</p>
      </div>
      <div className="relative max-w-xl">
        <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
        <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search parent or student registration" />
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {loading ? <p className="py-8 text-center text-sm text-slate-500">Loading parents...</p> : null}
      {!loading && !filteredParents.length ? <p className="py-8 text-center text-sm text-slate-500">No parents found.</p> : null}
      {!loading && filteredParents.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-3">Parent / Guardian</th>
                <th className="px-3 py-3">Linked Students</th>
                <th className="px-3 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredParents.map((parent) => (
                <tr key={parent.id}>
                  <td className="px-3 py-3 font-medium">{parent.name}</td>
                  <td className="px-3 py-3 text-slate-600">{parent.children?.length ? parent.children.join(", ") : "None"}</td>
                  <td className="px-3 py-3 text-right">
                    <button onClick={() => remove(parent)} className="inline-flex items-center justify-center gap-2 rounded-md p-2 text-sm font-semibold text-coral">
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </Card>
  );
}
