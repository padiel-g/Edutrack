import { AdminTimetableManager } from "@/components/timetables/AdminTimetableManager";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Timetable Management</h1>
        <p className="text-slate-500">Choose whether to create a learning timetable or an exam timetable.</p>
      </div>
      <AdminTimetableManager />
    </div>
  );
}
