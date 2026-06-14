import Link from "next/link";
import { ArrowRight, BarChart3, ClipboardCheck, CreditCard, GraduationCap } from "lucide-react";

export default function LandingPage() {
  const features = [
    { label: "Academics", Icon: GraduationCap },
    { label: "Attendance", Icon: ClipboardCheck },
    { label: "Finance", Icon: CreditCard },
    { label: "Analytics", Icon: BarChart3 }
  ];

  return (
    <main className="min-h-screen bg-white">
      <section className="relative overflow-hidden bg-ink text-white">
        <div className="mx-auto grid min-h-[92vh] max-w-7xl content-center gap-10 px-6 py-20 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-teal-200">EduTrack School Management</p>
            <h1 className="max-w-3xl text-5xl font-bold leading-tight md:text-7xl">EduTrack</h1>
            <p className="mt-5 max-w-2xl text-lg text-slate-200">A complete academic, attendance, finance, reporting, messaging, and analytics workspace for modern schools.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/login" className="inline-flex h-11 items-center gap-2 rounded-md bg-brand px-5 font-semibold text-white">
                Sign in <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/forgot-password" className="inline-flex h-11 items-center rounded-md border border-white/25 px-5 font-semibold text-white">Reset password</Link>
            </div>
          </div>
          <div className="grid gap-4 self-end md:grid-cols-2">
            {features.map(({ label, Icon }) => (
              <div key={label} className="rounded-lg border border-white/10 bg-white/10 p-5">
                <Icon className="mb-8 h-8 w-8 text-teal-200" />
                <p className="text-xl font-semibold">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
