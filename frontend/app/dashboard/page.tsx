"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser, roleHome } from "@/lib/auth";

export default function DashboardRedirect() {
  const router = useRouter();
  useEffect(() => {
    const user = getUser();
    router.replace(user ? roleHome[user.role] : "/login");
  }, [router]);
  return <p className="text-sm text-slate-500">Opening your portal...</p>;
}
