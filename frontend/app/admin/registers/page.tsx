import { AdminRegisters } from "@/components/attendance/AdminRegisters";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Attendance Registers</h1>
        <p className="text-slate-500">Select a class teacher and date to view the submitted class register.</p>
      </div>
      <AdminRegisters />
    </div>
  );
}
