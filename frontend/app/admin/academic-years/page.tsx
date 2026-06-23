import { AcademicYearsManager } from "@/components/academic-years/AcademicYearsManager";

export default function AcademicYearsPage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Academic Years and Terms</h1>
        <p className="mt-1 text-sm text-slate-500">Create academic years, add their terms, and delete unused calendar records.</p>
      </div>
      <AcademicYearsManager />
    </div>
  );
}
