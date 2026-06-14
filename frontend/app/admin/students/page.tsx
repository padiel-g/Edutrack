import { StudentsTable } from "@/components/tables/StudentsTable";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Student Management</h1>
        <p className="text-slate-500">Register students, assign classes, link guardians, and manage student records.</p>
      </div>
      <StudentsTable />
    </div>
  );
}
