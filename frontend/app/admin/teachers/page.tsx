import { TeachersTable } from "@/components/teachers/TeachersTable";

export default function Page() {
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Teacher Management</h1><p className="text-slate-500">Create teacher accounts and manage access.</p></div><TeachersTable /></div>;
}
