"use client";

import { Search } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type FeeAccount = {
  id: number;
  accountNumber: string;
  currentBalance: number;
  status: string;
  student: {
    registrationNumber?: string;
    name?: string;
    class?: string;
    gradeForm?: string;
    classStream?: string;
  } | null;
};

const gradeForms = ["Form 1", "Form 2", "Form 3", "Form 4", "Form 5", "Form 6"];
const classStreams = ["Sciences", "Commercials", "Arts", "General", "Technical", "Agriculture"];

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export function StudentFeeAccountsByClass() {
  const [gradeForm, setGradeForm] = useState("");
  const [classStream, setClassStream] = useState("");
  const [items, setItems] = useState<FeeAccount[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadAccounts(selectedGradeForm = gradeForm, selectedClassStream = classStream) {
    if (!selectedGradeForm || !selectedClassStream) {
      setItems([]);
      return;
    }

    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams({
        gradeForm: selectedGradeForm,
        classStream: selectedClassStream,
        search,
        perPage: "100",
      });
      const response = await api<{ items: FeeAccount[] }>(`/student-fee-accounts?${query}`);
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load student accounts");
    } finally {
      setLoading(false);
    }
  }

  function selectGradeForm(value: string) {
    setGradeForm(value);
    setSearch("");
    setItems([]);
  }

  function selectClassStream(value: string) {
    setClassStream(value);
    setSearch("");
    setItems([]);
  }

  const filtersReady = Boolean(gradeForm && classStream);

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Student Fee Accounts</h2>
        <p className="text-sm text-slate-500">Select both a form and stream before viewing student accounts.</p>
      </div>

      <div className="grid gap-3 lg:grid-cols-[200px_220px_1fr_120px]">
        <select
          value={gradeForm}
          onChange={(event) => selectGradeForm(event.target.value)}
          className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
          aria-label="Select form"
        >
          <option value="">Select form</option>
          {gradeForms.map((form) => (
            <option key={form} value={form}>{form}</option>
          ))}
        </select>
        <select
          value={classStream}
          onChange={(event) => selectClassStream(event.target.value)}
          className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
          aria-label="Select stream"
        >
          <option value="">Select class / stream</option>
          {classStreams.map((stream) => (
            <option key={stream} value={stream}>{stream}</option>
          ))}
        </select>
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && filtersReady) void loadAccounts();
            }}
            placeholder="Search student or account number"
            disabled={!filtersReady}
          />
        </div>
        <Button onClick={() => loadAccounts()} disabled={!filtersReady || loading}>View Accounts</Button>
      </div>

      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {!filtersReady ? (
        <p className="rounded-md border border-dashed border-slate-300 py-10 text-center text-sm text-slate-500">
          Choose a form and stream, for example Form 5 and Arts, then click View Accounts.
        </p>
      ) : null}
      {loading ? <p className="py-8 text-center text-sm text-slate-500">Loading accounts...</p> : null}
      {filtersReady && !loading && !items.length ? (
        <p className="py-8 text-center text-sm text-slate-500">No fee accounts found for {gradeForm} {classStream}.</p>
      ) : null}
      {!loading && items.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-3">Account Number</th>
                <th className="px-3 py-3">Registration Number</th>
                <th className="px-3 py-3">Student</th>
                <th className="px-3 py-3">Form</th>
                <th className="px-3 py-3">Stream</th>
                <th className="px-3 py-3">Balance</th>
                <th className="px-3 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((account) => (
                <tr key={account.id}>
                  <td className="px-3 py-3 font-medium">{account.accountNumber}</td>
                  <td className="px-3 py-3">{account.student?.registrationNumber ?? "-"}</td>
                  <td className="px-3 py-3">{account.student?.name ?? "-"}</td>
                  <td className="px-3 py-3">{account.student?.gradeForm ?? "-"}</td>
                  <td className="px-3 py-3">{account.student?.classStream ?? "-"}</td>
                  <td className="px-3 py-3">{money(account.currentBalance)}</td>
                  <td className="px-3 py-3">{account.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </Card>
  );
}
