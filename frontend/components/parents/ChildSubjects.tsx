"use client";

import { BookOpen, GraduationCap } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import type { Student } from "@/types/student";

export function ChildSubjects() {
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: Student[] }>("/students?perPage=1")
      .then((response) => setStudent(response.items[0] ?? null))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load student subjects"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">My Child</h1>
        <p className="text-slate-500">Student details and enrolled subjects.</p>
      </div>

      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {loading ? <Card><p className="py-8 text-center text-sm text-slate-500">Loading student information...</p></Card> : null}
      {!loading && !student ? <Card><p className="py-8 text-center text-sm text-slate-500">No student record is linked to this parent login.</p></Card> : null}

      {student ? (
        <>
          <Card>
            <div className="flex items-start gap-3">
              <GraduationCap className="mt-1 h-5 w-5 text-brand" />
              <div>
                <h2 className="text-lg font-semibold">{student.name}</h2>
                <p className="text-sm text-slate-500">{student.registrationNumber}</p>
                <p className="mt-2 text-sm">
                  {student.gradeForm || "Grade not assigned"}
                  {" · "}
                  {student.classStream || student.classType || student.class || "Class not assigned"}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <h2 className="text-lg font-semibold">Subjects Being Taken</h2>
                <p className="text-sm text-slate-500">Subjects registered for {student.firstName}.</p>
              </div>
              <span className="text-sm font-semibold text-brand">{student.subjects?.length ?? 0} subjects</span>
            </div>

            {student.subjects?.length ? (
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {student.subjects.map((subject) => (
                  <div key={subject.id} className="flex items-center gap-3 rounded-md border border-slate-200 p-3">
                    <BookOpen className="h-4 w-4 shrink-0 text-brand" />
                    <div className="min-w-0">
                      <p className="font-medium">{subject.name}</p>
                      <p className="text-xs text-slate-500">{subject.code}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-slate-500">No subjects have been assigned to this student yet.</p>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
