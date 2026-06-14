"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiDownload } from "@/lib/api";

export default function FinanceReportsPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function download() {
    setError("");
    setLoading(true);
    try {
      const blob = await apiDownload("/pdf/finance-report");
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "edutrack-finance-report.pdf";
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to download the finance report.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Finance Reports</h1>
        <p className="text-slate-500">Download a summary of invoiced fees, payments, and outstanding balances.</p>
      </div>
      <Card className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Fee Collection Summary</h2>
          <p className="text-sm text-slate-500">This report contains financial totals only. Academic results are not available in the Accounts portal.</p>
        </div>
        {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        <Button onClick={download} disabled={loading}>
          <Download className="h-4 w-4" />
          {loading ? "Preparing report..." : "Download PDF"}
        </Button>
      </Card>
    </div>
  );
}
