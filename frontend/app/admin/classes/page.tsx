import { ClassesManager } from "@/components/classes/ClassesManager";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Classes</h1>
        <p className="text-slate-500">Create school-defined classes and monitor students, subjects, teachers, and class teachers.</p>
      </div>
      <ClassesManager />
    </div>
  );
}
