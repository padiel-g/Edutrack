"use client";

import { BookOpen, ClipboardList } from "lucide-react";
import { useState } from "react";
import { ExamTimetableManager } from "@/components/timetables/ExamTimetableManager";
import { LearningTimetableManager } from "@/components/timetables/LearningTimetableManager";

type TimetableType = "learning" | "exam";

export function AdminTimetableManager() {
  const [type, setType] = useState<TimetableType>("learning");

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => setType("learning")}
          className={`flex items-center gap-3 rounded-xl border p-4 text-left transition ${type === "learning" ? "border-brand bg-teal-50" : "border-slate-200 bg-white hover:border-slate-300"}`}
        >
          <BookOpen className="h-6 w-6 text-brand" />
          <span><span className="block font-semibold">Learning Timetable</span><span className="text-sm text-slate-500">Schedule normal class lessons.</span></span>
        </button>
        <button
          type="button"
          onClick={() => setType("exam")}
          className={`flex items-center gap-3 rounded-xl border p-4 text-left transition ${type === "exam" ? "border-brand bg-teal-50" : "border-slate-200 bg-white hover:border-slate-300"}`}
        >
          <ClipboardList className="h-6 w-6 text-brand" />
          <span><span className="block font-semibold">Exam Timetable</span><span className="text-sm text-slate-500">Schedule examination papers.</span></span>
        </button>
      </div>
      {type === "learning" ? <LearningTimetableManager /> : <ExamTimetableManager canManage />}
    </div>
  );
}
