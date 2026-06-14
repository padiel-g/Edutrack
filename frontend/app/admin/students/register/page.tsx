import { StudentRegistrationForm } from "@/components/forms/StudentRegistrationForm";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Register Student</h1>
      </div>
      <StudentRegistrationForm />
    </div>
  );
}
