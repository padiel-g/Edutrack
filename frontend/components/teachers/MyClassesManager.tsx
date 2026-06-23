"use client";

import { BookOpen, GraduationCap, Star, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

type Subject = { id: number; code: string; name: string };
type SchoolClass = {
  id: number;
  name: string;
  gradeLevel: string;
  capacity: number;
  studentCount: number;
  isClassTeacher: boolean;
  subjects: Subject[];
};
type Response = {
  teacher: { name: string; employeeNumber: string };
  items: SchoolClass[];
};

export function MyClassesManager() {
  const [data, setData] = useState<Response | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Response>("/teacher/classes")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load assigned classes"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">My Classes</h1>
        <p className="text-slate-500">Classes assigned to you by the school administrator.</p>
      </div>

      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
      {loading ? <Card><p className="py-10 text-center text-sm text-slate-500">Loading assigned classes...</p></Card> : null}

      {!loading && !data?.items.length ? (
        <Card>
          <div className="grid min-h-64 place-items-center text-center">
            <div>
              <GraduationCap className="mx-auto h-12 w-12 text-slate-300" />
              <h2 className="mt-4 text-lg font-semibold">No classes assigned</h2>
              <p className="mt-1 max-w-md text-sm text-slate-500">
                An administrator must assign classes and subjects to your teacher profile.
              </p>
            </div>
          </div>
        </Card>
      ) : null}

      {data?.items.length ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Summary label="Assigned classes" value={data.items.length} icon={<GraduationCap className="h-5 w-5" />} />
            <Summary label="Total learners" value={data.items.reduce((sum, item) => sum + item.studentCount, 0)} icon={<Users className="h-5 w-5" />} />
            <Summary label="Class Teacher roles" value={data.items.filter((item) => item.isClassTeacher).length} icon={<Star className="h-5 w-5" />} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {data.items.map((schoolClass) => (
              <Card key={schoolClass.id} className="overflow-hidden p-0">
                <div className="bg-slate-900 px-5 py-4 text-white">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-wider text-slate-300">{schoolClass.gradeLevel}</p>
                      <h2 className="mt-1 text-xl font-bold">{schoolClass.name}</h2>
                    </div>
                    {schoolClass.isClassTeacher ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-300 px-2.5 py-1 text-xs font-semibold text-slate-900">
                        <Star className="h-3.5 w-3.5" /> Class Teacher
                      </span>
                    ) : null}
                  </div>
                </div>
                <div className="p-5">
                  <div className="grid grid-cols-2 gap-3">
                    <Metric label="Learners" value={`${schoolClass.studentCount}`} icon={<Users className="h-4 w-4" />} />
                    <Metric label="Capacity" value={`${schoolClass.capacity}`} icon={<GraduationCap className="h-4 w-4" />} />
                  </div>
                  <div className="mt-5">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <BookOpen className="h-4 w-4 text-brand" /> Teaching subjects
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {schoolClass.subjects.length ? schoolClass.subjects.map((subject) => (
                        <span key={subject.id} className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-800">
                          {subject.code} - {subject.name}
                        </span>
                      )) : <span className="text-sm text-slate-500">No subjects assigned for this class.</span>}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

function Summary({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return <Card><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-lg bg-teal-50 text-brand">{icon}</span><div><p className="text-sm text-slate-500">{label}</p><p className="text-2xl font-bold">{value}</p></div></div></Card>;
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return <div className="rounded-lg bg-slate-50 p-3"><div className="flex items-center gap-1.5 text-xs text-slate-500">{icon}{label}</div><p className="mt-1 text-lg font-bold">{value}</p></div>;
}
