import { AdminParentsManager } from "@/components/parents/AdminParentsManager";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Parent Management</h1>
        <p className="text-slate-500">Review linked guardians and remove parent records from the admin portal.</p>
      </div>
      <AdminParentsManager />
    </div>
  );
}
