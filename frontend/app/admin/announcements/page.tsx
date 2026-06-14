import { AnnouncementsManager } from "@/components/announcements/AnnouncementsManager";

export default function AnnouncementsPage() {
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-bold">Announcements</h1><p className="text-slate-500">Post written or video announcements to teachers and parents.</p></div>
      <AnnouncementsManager />
    </div>
  );
}
