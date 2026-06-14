import { AnnouncementFeed } from "@/components/announcements/AnnouncementFeed";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Announcements</h1>
        <p className="text-slate-500">Announcements posted for all teachers or specifically for you.</p>
      </div>
      <AnnouncementFeed showAll />
    </div>
  );
}
