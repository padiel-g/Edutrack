import { SubjectsManager } from "@/components/subjects/SubjectsManager";

export default function SubjectsPage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Subject Management</h1>
        <p className="mt-1 text-sm text-slate-500">Add subjects and remove subjects that are no longer in use.</p>
      </div>
      <SubjectsManager />
    </div>
  );
}
