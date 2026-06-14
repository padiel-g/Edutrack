"use client";

import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { api, apiDownload } from "@/lib/api";
import { Card } from "@/components/ui/Card";

type Announcement = { id: number; title: string; body: string; publishedAt: string; hasVideo: boolean };

export function AnnouncementFeed({ showPopup = false, showAll = false }: { showPopup?: boolean; showAll?: boolean }) {
  const [items, setItems] = useState<Announcement[]>([]);
  const [popup, setPopup] = useState<Announcement | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: Announcement[] }>("/announcements").then(({ items }) => {
      setItems(items);
      const newest = items[0];
      if (showPopup && newest && localStorage.getItem("lastSeenAnnouncement") !== String(newest.id)) {
        setPopup(newest);
      }
    }).catch((err) => setError(err instanceof Error ? err.message : "Unable to load announcements"));
  }, [showPopup]);

  function closePopup() {
    if (popup) localStorage.setItem("lastSeenAnnouncement", String(popup.id));
    setPopup(null);
  }

  return (
    <>
      <Card>
        <h3 className="font-semibold">Announcements</h3>
        {error ? <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        <div className="mt-3 space-y-3">
          {(showAll ? items : items.slice(0, 5)).map((item) => <AnnouncementContent key={item.id} item={item} />)}
          {!items.length && !error ? <p className="text-sm text-slate-500">No announcements posted for you.</p> : null}
        </div>
      </Card>
      {popup ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
          <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between gap-3">
              <div><p className="text-xs font-semibold uppercase tracking-wide text-brand">New announcement</p><h2 className="mt-1 text-xl font-bold">{popup.title}</h2></div>
              <button onClick={closePopup} className="rounded-md p-2 hover:bg-slate-100" aria-label="Close announcement"><X className="h-5 w-5" /></button>
            </div>
            <div className="mt-4"><AnnouncementContent item={popup} /></div>
          </div>
        </div>
      ) : null}
    </>
  );
}

function AnnouncementContent({ item }: { item: Announcement }) {
  const [videoUrl, setVideoUrl] = useState("");
  useEffect(() => {
    if (!item.hasVideo) return;
    let active = true;
    apiDownload(`/announcements/${item.id}/video`).then((blob) => {
      if (active) setVideoUrl(URL.createObjectURL(blob));
    }).catch(() => undefined);
    return () => {
      active = false;
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [item.id, item.hasVideo]);

  return (
    <article className="rounded-lg border border-slate-100 p-3">
      <h4 className="font-semibold">{item.title}</h4>
      <p className="text-xs text-slate-400">{new Date(item.publishedAt).toLocaleString()}</p>
      {item.body ? <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{item.body}</p> : null}
      {videoUrl ? <video className="mt-3 max-h-80 w-full rounded-lg bg-black" controls src={videoUrl} /> : null}
    </article>
  );
}
