"use client";

import { BookOpen, Download, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { api, apiDownload } from "@/lib/api";
import { Card } from "@/components/ui/Card";

type Subject = { id: number; code: string; name: string };
type Material = {
  id: number;
  title: string;
  description?: string;
  subject: Subject;
  teacherName?: string;
  originalFilename?: string;
  fileSize?: number;
  downloadUrl: string;
  createdAt?: string;
};

function fileSize(value?: number) {
  if (!value) return "-";
  if (value < 1024 * 1024) return `${Math.ceil(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function ParentLearningMaterials() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: Material[] }>("/teacher/learning-materials")
      .then((response) => setMaterials(response.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load learning materials"))
      .finally(() => setLoading(false));
  }, []);

  async function download(material: Material) {
    setError("");
    try {
      const blob = await apiDownload(material.downloadUrl);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = material.originalFilename || material.title;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to download learning material");
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Learning Materials</h1>
        <p className="text-slate-500">Reading materials for subjects taken by the student linked to this login.</p>
      </div>
      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      <Card>
        {loading ? <p className="py-10 text-center text-sm text-slate-500">Loading learning materials...</p> : null}
        {!loading && !materials.length ? (
          <div className="py-10 text-center">
            <BookOpen className="mx-auto h-6 w-6 text-slate-400" />
            <p className="mt-2 text-sm text-slate-500">No materials have been uploaded for this student&apos;s subjects yet.</p>
          </div>
        ) : null}
        {materials.length ? (
          <div className="divide-y divide-slate-100">
            {materials.map((material) => (
              <div key={material.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 gap-3">
                  <FileText className="mt-1 h-5 w-5 shrink-0 text-brand" />
                  <div className="min-w-0">
                    <p className="font-semibold">{material.title}</p>
                    <p className="text-sm text-slate-600">{material.subject.code} - {material.subject.name}</p>
                    {material.description ? <p className="mt-1 text-sm text-slate-500">{material.description}</p> : null}
                    <p className="mt-1 truncate text-xs text-slate-400">
                      {material.originalFilename || "Reading material"} - {fileSize(material.fileSize)}
                      {material.teacherName ? ` - ${material.teacherName}` : ""}
                    </p>
                  </div>
                </div>
                <button type="button" onClick={() => download(material)} className="inline-flex h-10 items-center justify-center gap-2 self-end rounded-md bg-brand px-4 text-sm font-semibold text-white hover:bg-teal-800 sm:self-auto">
                  <Download className="h-4 w-4" />
                  Download
                </button>
              </div>
            ))}
          </div>
        ) : null}
      </Card>
    </div>
  );
}
