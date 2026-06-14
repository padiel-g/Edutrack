import { AccountsOfficerManager } from "@/components/accounts/AccountsOfficerManager";

export default function Page() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Accounts Management</h1>
        <p className="text-slate-500">Create and view Accounts Officer login accounts.</p>
      </div>
      <AccountsOfficerManager />
    </div>
  );
}
