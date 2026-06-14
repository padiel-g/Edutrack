"use client";

import { Megaphone, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type Target = { id: number; name: string; reference: string };
type Announcement = { id: number; title: string; body: string; audience: string; publishedAt: string; hasVideo: boolean };

export function AnnouncementsManager() {
  const [items, setItems] = useState<Announcement[]>([]);
  const [teachers, setTeachers] = useState<Target[]>([]);
  const [parents, setParents] = useState<Target[]>([]);
  const [audience, setAudience] = useState("teachers");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const results = await Promise.allSettled([
      api<{ items: Announcement[] }>("/announcements"),
      api<{ items: { id: number; name: string; employeeNumber: string }[] }>("/admin/teachers?perPage=100"),
      api<{ teachers: Target[]; parents: Target[] }>("/announcements/targets")
    ]);

    const [announcements, teacherResponse, targets] = results;
    if (announcements.status === "fulfilled") {
      setItems(announcements.value.items);
    }
    if (teacherResponse.status === "fulfilled") {
      setTeachers(
        teacherResponse.value.items.map((teacher) => ({
          id: teacher.id,
          name: teacher.name,
          reference: teacher.employeeNumber
        }))
      );
    } else if (targets.status === "fulfilled") {
      setTeachers(targets.value.teachers);
    }
    if (targets.status === "fulfilled") {
      setParents(targets.value.parents);
    }
    if (announcements.status === "rejected" && teacherResponse.status === "rejected" && targets.status === "rejected") {
      throw announcements.reason;
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load announcements"));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await api("/announcements", { method: "POST", body: data });
      form.reset();
      setAudience("teachers");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to post announcement");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    if (!window.confirm("Delete this announcement?")) return;
    await api(`/announcements/${id}`, { method: "DELETE" });
    setItems((current) => current.filter((item) => item.id !== id));
  }

  const specificTargets = audience === "teacher"
    ? [...teachers].sort((a, b) => a.name.localeCompare(b.name))
    : [...parents].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
      <Card>
        <div className="flex items-center gap-3"><Megaphone className="h-6 w-6 text-brand" /><h2 className="text-lg font-semibold">Post Announcement</h2></div>
        <form onSubmit={submit} className="mt-5 space-y-4">
          <label className="block space-y-1 text-sm font-medium">Title<Input name="title" required /></label>
          <label className="block space-y-1 text-sm font-medium">Written message
            <textarea name="body" className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Optional when posting a video" />
          </label>
          <label className="block space-y-1 text-sm font-medium">Video
            <Input name="video" type="file" accept="video/mp4,video/webm,video/quicktime,.m4v" />
          </label>
          <label className="block space-y-1 text-sm font-medium">Who can see it?
            <select name="audience" value={audience} onChange={(event) => setAudience(event.target.value)} className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              <option value="teachers">All teachers</option>
              <option value="parents">All parents</option>
              <option value="all">Teachers and parents</option>
              <option value="teacher">Specific teacher</option>
              <option value="parent">Specific parent</option>
            </select>
          </label>
          {audience === "teacher" || audience === "parent" ? (
            <label className="block space-y-1 text-sm font-medium">Recipient
              <select name="targetId" required className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
                <option value="">{specificTargets.length ? "Select recipient" : `No ${audience === "teacher" ? "teachers" : "parents"} found`}</option>
                {specificTargets.map((target) => <option key={target.id} value={target.id}>{target.name} ({target.reference})</option>)}
              </select>
            </label>
          ) : null}
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button className="w-full" disabled={loading}>{loading ? "Posting..." : "Post Announcement"}</Button>
        </form>
      </Card>
      <Card>
        <h2 className="text-lg font-semibold">Posted Announcements</h2>
        <div className="mt-4 space-y-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-start justify-between gap-3">
                <div><h3 className="font-semibold">{item.title}</h3><p className="text-xs text-slate-500">{item.audience} · {new Date(item.publishedAt).toLocaleString()}</p></div>
                <button onClick={() => remove(item.id)} className="p-2 text-red-600" aria-label="Delete announcement"><Trash2 className="h-4 w-4" /></button>
              </div>
              {item.body ? <p className="mt-3 whitespace-pre-wrap text-sm text-slate-600">{item.body}</p> : null}
              {item.hasVideo ? <p className="mt-2 text-xs font-semibold text-brand">Includes video</p> : null}
            </div>
          ))}
          {!items.length ? <p className="py-8 text-center text-sm text-slate-500">No announcements posted.</p> : null}
        </div>
      </Card>
    </div>
  );
}
