import { AnnouncementFeed } from "@/components/announcements/AnnouncementFeed";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Announcements</h1>
        <p className="text-slate-500">Announcements posted for parents or for the learner registration number used to sign in.</p>
      </div>
      <AnnouncementFeed showAll />
    </div>
  );
}
