"use client";

import { Download, FileText, Trash2, Upload } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { api, apiDownload } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Subject = { id: number; code: string; name: string };
type Material = {
  id: number;
  title: string;
  description?: string;
  subject: Subject;
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

export function LearningMaterialsManager() {
  const formRef = useRef<HTMLFormElement>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const response = await api<{ items: Material[]; assignedSubjects: Subject[] }>("/teacher/learning-materials");
      setSubjects(response.assignedSubjects);
      setMaterials(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load learning materials");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function uploadMaterial(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploading(true);
    setError("");
    setMessage("");
    try {
      const formData = new FormData(event.currentTarget);
      await api("/teacher/learning-materials", { method: "POST", body: formData });
      formRef.current?.reset();
      setMessage("Reading material uploaded successfully.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to upload material");
    } finally {
      setUploading(false);
    }
  }

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
      setError(err instanceof Error ? err.message : "Unable to download material");
    }
  }

  async function remove(material: Material) {
    if (!window.confirm(`Delete "${material.title}"?`)) return;
    try {
      await api(`/teacher/learning-materials/${material.id}`, { method: "DELETE" });
      setMessage("Learning material deleted.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete material");
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Learning Materials</h1>
        <p className="text-slate-500">Upload reading materials for subjects assigned to you.</p>
      </div>

      <Card>
        <h2 className="text-lg font-semibold">Upload Reading Material</h2>
        <form ref={formRef} onSubmit={uploadMaterial} className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm font-medium">
            Subject
            <select name="subjectId" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              <option value="">Select subject</option>
              {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.code} - {subject.name}</option>)}
            </select>
          </label>
          <label className="space-y-1 text-sm font-medium">Title<Input name="title" required placeholder="Material title" /></label>
          <label className="space-y-1 text-sm font-medium md:col-span-2">
            Description
            <textarea name="description" className="min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Optional description" />
          </label>
          <label className="space-y-1 text-sm font-medium md:col-span-2">
            File
            <Input name="file" type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.txt" required />
            <span className="block text-xs font-normal text-slate-500">PDF, Word, PowerPoint, or TXT. Maximum size is controlled by the server.</span>
          </label>
          {!subjects.length && !loading && !error ? <p className="text-sm text-amber-700 md:col-span-2">No subjects are currently assigned to this teacher account. Contact the administrator.</p> : null}
          <div className="md:col-span-2 md:flex md:justify-end">
            <Button disabled={uploading || !subjects.length}><Upload className="h-4 w-4" />{uploading ? "Uploading..." : "Upload Material"}</Button>
          </div>
        </form>
      </Card>

      {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {message ? <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p> : null}

      <Card>
        <h2 className="text-lg font-semibold">Uploaded Materials</h2>
        {loading ? <p className="py-8 text-center text-sm text-slate-500">Loading materials...</p> : null}
        {!loading && !materials.length ? <p className="py-8 text-center text-sm text-slate-500">No learning materials have been uploaded yet.</p> : null}
        {materials.length ? (
          <div className="mt-4 divide-y divide-slate-100">
            {materials.map((material) => (
              <div key={material.id} className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 gap-3">
                  <FileText className="mt-1 h-5 w-5 shrink-0 text-brand" />
                  <div className="min-w-0">
                    <p className="font-semibold">{material.title}</p>
                    <p className="text-sm text-slate-500">{material.subject.code} - {material.subject.name}</p>
                    <p className="truncate text-xs text-slate-400">{material.originalFilename} · {fileSize(material.fileSize)}</p>
                  </div>
                </div>
                <div className="flex gap-1 self-end sm:self-auto">
                  <button type="button" onClick={() => download(material)} className="rounded-md p-2 hover:bg-slate-100" title="Download"><Download className="h-4 w-4" /></button>
                  <button type="button" onClick={() => remove(material)} className="rounded-md p-2 text-coral hover:bg-red-50" title="Delete"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </Card>
    </div>
  );
}
