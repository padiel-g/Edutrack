"use client";

import { Download, Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { api, apiDownload } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type StudentSummary = {
  id: number;
  registrationNumber: string;
  name: string;
  form?: string;
  class?: string;
  stream?: string;
  guardian?: string;
  currentBalance: number;
  totalFee: number;
  totalPaid: number;
  status: string;
  currentTerm?: { id: number; name: string; academicYear?: string };
};

type Receipt = {
  id: number;
  receiptNumber: string;
  issuedAt: string;
  downloadUrl: string;
};

type Payment = {
  id: number;
  paymentReference: string;
  referenceNumber?: string;
  amount: number;
  method: string;
  term?: string;
  previousBalance: number;
  newBalance: number;
  paidAt: string;
  recordedBy?: string;
  student?: { registrationNumber?: string; name?: string; gradeForm?: string; classStream?: string };
  receipt?: Receipt;
};

type SearchResponse = {
  student: StudentSummary;
  terms: { id: number; name: string; academicYear?: string; isCurrent: boolean }[];
};

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

async function downloadReceipt(receipt: Receipt) {
  const blob = await apiDownload(receipt.downloadUrl);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${receipt.receiptNumber}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}

export function RecordPaymentForm() {
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [student, setStudent] = useState<StudentSummary | null>(null);
  const [terms, setTerms] = useState<SearchResponse["terms"]>([]);
  const [termName, setTermName] = useState("");
  const [totalFee, setTotalFee] = useState("");
  const [amount, setAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10));
  const [referenceNumber, setReferenceNumber] = useState("");
  const [note, setNote] = useState("");
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function findStudent() {
    if (!registrationNumber.trim()) return setError("Enter a student registration number.");
    setLoading(true);
    setError("");
    setReceipt(null);
    try {
      const response = await api<SearchResponse>(`/accounts/students/search?reg_number=${encodeURIComponent(registrationNumber.trim())}`);
      setStudent(response.student);
      setTerms(response.terms);
      setTermName(response.student.currentTerm?.name ?? response.terms.find((item) => item.isCurrent)?.name ?? "");
    } catch (err) {
      setStudent(null);
      setError(err instanceof Error ? err.message : "Student not found");
    } finally {
      setLoading(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!student) return setError("Search for a valid student first.");
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const response = await api<{ message: string; payment: Payment; receipt: Receipt; account: { currentBalance: number; totalPaid: number; status: string } }>("/accounts/payments", {
        method: "POST",
        body: JSON.stringify({
          registrationNumber: student.registrationNumber,
          termName,
          totalFee: student.currentBalance <= 0 ? Number(totalFee) : undefined,
          amount: Number(amount),
          paymentMethod,
          paymentDate,
          referenceNumber,
          note,
        }),
      });
      setPayment(response.payment);
      setReceipt(response.receipt);
      setStudent({ ...student, currentBalance: response.account.currentBalance, totalPaid: response.account.totalPaid, status: response.account.status });
      setSuccess(response.message);
      setTotalFee("");
      setAmount("");
      setReferenceNumber("");
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to record payment");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
      <Card className="space-y-5">
        <div>
          <h2 className="text-lg font-semibold">Find Student</h2>
          <p className="text-sm text-slate-500">Enter the exact registration number to load the fee account.</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Input value={registrationNumber} onChange={(event) => setRegistrationNumber(event.target.value)} onKeyDown={(event) => event.key === "Enter" && findStudent()} placeholder="EDU-2026-0001" />
          <Button type="button" onClick={findStudent} disabled={loading}><Search className="h-4 w-4" />Search</Button>
        </div>
        {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</p> : null}
        {student ? (
          <>
            <div className="grid gap-3 rounded-lg bg-slate-50 p-4 sm:grid-cols-2">
              <Detail label="Student" value={student.name} />
              <Detail label="Registration" value={student.registrationNumber} />
              <Detail label="Form / Class" value={[student.form || student.class, student.stream].filter(Boolean).join(" - ")} />
              <Detail label="Parent / Guardian" value={student.guardian || "-"} />
              <Detail label="Current term" value={student.currentTerm?.name || "-"} />
              <Detail label="Current balance" value={money(student.currentBalance)} strong />
            </div>
            <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
              <Field label="Term">
                <Input
                  value={termName}
                  onChange={(event) => setTermName(event.target.value)}
                  placeholder="Enter term, e.g. Term 1"
                  list="payment-terms"
                  required
                />
                <datalist id="payment-terms">
                  {terms.map((term) => <option key={term.id} value={term.name}>{term.academicYear}</option>)}
                </datalist>
              </Field>
              {student.currentBalance <= 0 ? (
                <Field label="Amount due / total fee">
                  <Input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={totalFee}
                    onChange={(event) => setTotalFee(event.target.value)}
                    placeholder="Enter the student's fee balance"
                    required
                  />
                </Field>
              ) : null}
              <Field label="Amount paid"><Input type="number" min="0.01" max={student.currentBalance > 0 ? student.currentBalance : Number(totalFee) || undefined} step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required /></Field>
              <Field label="Payment method">
                <select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)} className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                  {["Cash", "Bank Transfer", "Card", "Mobile Money", "Cheque"].map((method) => <option key={method}>{method}</option>)}
                </select>
              </Field>
              <Field label="Payment date"><Input type="date" value={paymentDate} onChange={(event) => setPaymentDate(event.target.value)} required /></Field>
              <Field label="Reference number (optional)"><Input value={referenceNumber} onChange={(event) => setReferenceNumber(event.target.value)} /></Field>
              <Field label="Note (optional)"><Input value={note} onChange={(event) => setNote(event.target.value)} /></Field>
              <Button className="sm:col-span-2" disabled={loading || (student.currentBalance <= 0 && Number(totalFee) <= 0)}>{loading ? "Saving payment..." : "Record Payment & Generate Receipt"}</Button>
            </form>
          </>
        ) : null}
      </Card>
      <Card>
        <h2 className="text-lg font-semibold">Receipt Preview</h2>
        {!receipt || !payment || !student ? <p className="mt-4 text-sm text-slate-500">The generated receipt will appear here after payment.</p> : (
          <div className="mt-4 space-y-3">
            <p className="text-center text-xl font-bold">EduTrack School</p>
            <p className="text-center text-sm text-slate-500">Official Fee Payment Receipt</p>
            <div className="divide-y text-sm">
              <DetailRow label="Receipt" value={receipt.receiptNumber} />
              <DetailRow label="Student" value={student.name} />
              <DetailRow label="Registration" value={student.registrationNumber} />
              <DetailRow label="Term" value={payment.term || "-"} />
              <DetailRow label="Amount paid" value={money(payment.amount)} />
              <DetailRow label="Previous balance" value={money(payment.previousBalance)} />
              <DetailRow label="New balance" value={money(payment.newBalance)} />
              <DetailRow label="Method" value={payment.method} />
              <DetailRow label="Accountant" value={payment.recordedBy || getUser()?.name || "-"} />
            </div>
            <Button className="w-full" onClick={() => downloadReceipt(receipt)}><Download className="h-4 w-4" />Download / Print PDF</Button>
          </div>
        )}
      </Card>
    </div>
  );
}

export function PaymentHistory({ parent = false }: { parent?: boolean }) {
  const [student, setStudent] = useState<StudentSummary | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const path = parent ? `/parents/children/${getUser()?.id}/payments` : "/accounts/payments";
    api<{ student?: StudentSummary; payments?: Payment[]; items?: Payment[] }>(path)
      .then((response) => { setStudent(response.student ?? null); setPayments(response.payments ?? response.items ?? []); })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load payments"))
      .finally(() => setLoading(false));
  }, [parent]);

  return (
    <div className="space-y-5">
      {student ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Summary label="Total fees" value={money(student.totalFee)} /><Summary label="Total paid" value={money(student.totalPaid)} /><Summary label="Balance" value={money(student.currentBalance)} /><Summary label="Status" value={student.status} /></div> : null}
      <Card>
        <h2 className="text-lg font-semibold">Payment History & Receipts</h2>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="mt-4 text-sm text-slate-500">Loading payments...</p> : null}
        {!loading && !payments.length ? <p className="mt-4 text-sm text-slate-500">No payments recorded.</p> : null}
        {payments.length ? <PaymentTable payments={payments} /> : null}
      </Card>
    </div>
  );
}

export function AdminFeesOverview() {
  const [items, setItems] = useState<{ id: number; totalFee: number; totalPaid: number; currentBalance: number; status: string; term?: string; student: StudentSummary }[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { api<{ items: typeof items }>("/admin/payments/summary").then((data) => setItems(data.items)).catch((err) => setError(err instanceof Error ? err.message : "Unable to load fees")); }, []);
  return <Card><h2 className="text-lg font-semibold">All Student Fee Accounts</h2>{error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}<div className="mt-4 overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Student</th><th className="p-3">Registration</th><th className="p-3">Form / Stream</th><th className="p-3">Term</th><th className="p-3">Total Fee</th><th className="p-3">Paid</th><th className="p-3">Balance</th><th className="p-3">Status</th></tr></thead><tbody className="divide-y">{items.map((item) => <tr key={item.id}><td className="p-3">{item.student.name}</td><td className="p-3">{item.student.registrationNumber}</td><td className="p-3">{[item.student.form, item.student.stream].filter(Boolean).join(" - ")}</td><td className="p-3">{item.term || "-"}</td><td className="p-3">{money(item.totalFee)}</td><td className="p-3">{money(item.totalPaid)}</td><td className="p-3">{money(item.currentBalance)}</td><td className="p-3">{item.status}</td></tr>)}</tbody></table></div></Card>;
}

function PaymentTable({ payments }: { payments: Payment[] }) {
  return <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Date</th><th className="p-3">Student</th><th className="p-3">Term</th><th className="p-3">Amount</th><th className="p-3">Method</th><th className="p-3">Reference</th><th className="p-3">Balance</th><th className="p-3">Receipt</th></tr></thead><tbody className="divide-y">{payments.map((payment) => <tr key={payment.id}><td className="p-3">{new Date(payment.paidAt).toLocaleDateString()}</td><td className="p-3">{payment.student?.name || payment.student?.registrationNumber || "-"}</td><td className="p-3">{payment.term || "-"}</td><td className="p-3">{money(payment.amount)}</td><td className="p-3">{payment.method}</td><td className="p-3">{payment.referenceNumber || payment.paymentReference}</td><td className="p-3">{money(payment.newBalance)}</td><td className="p-3">{payment.receipt ? <button className="font-semibold text-brand" onClick={() => downloadReceipt(payment.receipt!)}>Download {payment.receipt.receiptNumber}</button> : "-"}</td></tr>)}</tbody></table></div>;
}

function Detail({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) { return <div><p className="text-xs uppercase text-slate-500">{label}</p><p className={strong ? "mt-1 text-lg font-bold" : "mt-1 font-medium"}>{value || "-"}</p></div>; }
function DetailRow({ label, value }: { label: string; value: string }) { return <div className="flex justify-between gap-4 py-2"><span className="text-slate-500">{label}</span><span className="text-right font-medium">{value}</span></div>; }
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="space-y-1 text-sm font-medium"><span>{label}</span>{children}</label>; }
function Summary({ label, value }: { label: string; value: string }) { return <Card><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p></Card>; }
