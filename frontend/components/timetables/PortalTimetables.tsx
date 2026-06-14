"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

type Subject = { code: string; name: string };
type LearningEntry = {
  id: number;
  class?: { name: string };
  subject?: Subject;
  teacher?: { name: string };
  dayOfWeek: string;
  startTime: string;
  endTime: string;
};
type ExamEntry = {
  id: number;
  examDate: string;
  classType: string;
  subject?: Subject;
  paper?: string;
  startTime: string;
  endTime: string;
  venue?: string;
};
type Payload = {
  learner?: { name: string; registrationNumber: string; class?: string };
  learningTimetable: LearningEntry[];
  examTimetable: ExamEntry[];
};

export function PortalTimetables() {
  const [data, setData] = useState<Payload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Payload>("/portal/timetables")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load timetables"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Timetables</h1>
        <p className="text-slate-500">
          {data?.learner
            ? `${data.learner.name} (${data.learner.registrationNumber}) - ${data.learner.class || "Class not assigned"}`
            : "Your assigned learning and exam schedules."}
        </p>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
      {!data && !error ? <Card><p className="py-8 text-center text-sm text-slate-500">Loading timetables...</p></Card> : null}
      {data ? (
        <>
          <TimetableCard title="Learning Timetable" empty="No learning timetable is available." count={data.learningTimetable.length}>
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-3">Day</th><th className="px-3 py-3">Class</th><th className="px-3 py-3">Subject</th><th className="px-3 py-3">Teacher</th><th className="px-3 py-3">Time</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.learningTimetable.map((entry) => <tr key={entry.id}><td className="px-3 py-3 font-medium">{entry.dayOfWeek}</td><td className="px-3 py-3">{entry.class?.name || "-"}</td><td className="px-3 py-3">{entry.subject?.name || "-"}</td><td className="px-3 py-3">{entry.teacher?.name || "-"}</td><td className="px-3 py-3">{entry.startTime} - {entry.endTime}</td></tr>)}
              </tbody>
            </table>
          </TimetableCard>
          <TimetableCard title="Exam Timetable" empty="No exam timetable is available." count={data.examTimetable.length}>
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-3">Date</th><th className="px-3 py-3">Class</th><th className="px-3 py-3">Subject</th><th className="px-3 py-3">Paper</th><th className="px-3 py-3">Time</th><th className="px-3 py-3">Venue</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.examTimetable.map((entry) => <tr key={entry.id}><td className="px-3 py-3">{new Date(`${entry.examDate}T00:00:00`).toLocaleDateString()}</td><td className="px-3 py-3">{entry.classType}</td><td className="px-3 py-3 font-medium">{entry.subject?.name || "-"}</td><td className="px-3 py-3">{entry.paper || "-"}</td><td className="px-3 py-3">{entry.startTime} - {entry.endTime}</td><td className="px-3 py-3">{entry.venue || "-"}</td></tr>)}
              </tbody>
            </table>
          </TimetableCard>
        </>
      ) : null}
    </div>
  );
}

function TimetableCard({ title, empty, count, children }: { title: string; empty: string; count: number; children: React.ReactNode }) {
  return <Card><h2 className="text-lg font-semibold">{title}</h2>{count === 0 ? <p className="py-8 text-center text-sm text-slate-500">{empty}</p> : <div className="mt-4 overflow-x-auto">{children}</div>}</Card>;
}
