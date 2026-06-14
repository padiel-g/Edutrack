import { RegisterMarker } from "@/components/attendance/RegisterMarker";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Attendance Register</h1>
        <p className="text-slate-500">Mark each student Present or Absent. Submitting the register locks it for the day.</p>
      </div>
      <RegisterMarker />
    </div>
  );
}
