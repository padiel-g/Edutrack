import { ParentAttendance } from "@/components/attendance/ParentAttendance";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Child Attendance</h1>
        <p className="text-slate-500">Attendance for the student registration number used to sign in.</p>
      </div>
      <ParentAttendance />
    </div>
  );
}
