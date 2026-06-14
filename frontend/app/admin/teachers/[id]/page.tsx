import { TeacherForm } from "@/components/teachers/TeacherForm";

export default function Page({ params }: { params: { id: string } }) {
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold">Teacher Profile</h1></div><TeacherForm teacherId={Number(params.id)} /></div>;
}
