import { ClassesManager } from "@/components/classes/ClassesManager";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Classes</h1>
        <p className="text-slate-500">View each class and assign its teaching staff and Class Teacher.</p>
      </div>
      <ClassesManager />
    </div>
  );
}
