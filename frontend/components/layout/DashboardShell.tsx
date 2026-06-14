"use client";

import { LogOut, Menu, Search } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { expireSession, logout, getToken, getUser, isTokenExpired, restoreSessionCookies, roleHome } from "@/lib/auth";
import { navByRole } from "@/components/layout/nav";
import type { User } from "@/types";

const portalRoles: Record<string, User["role"][]> = {
  "/admin": ["Admin", "Super Admin"],
  "/teacher": ["Teacher"],
  "/student": ["Student"],
  "/parent": ["Parent"],
  "/accounts": ["Accounts Officer", "Admin", "Super Admin"]
};

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const sessionUser = getUser();
    const token = getToken();
    if (!sessionUser || !token) {
      router.replace("/login");
      return;
    }
    if (isTokenExpired(token)) {
      expireSession();
      return;
    }
    const portal = Object.keys(portalRoles).find((prefix) => pathname.startsWith(prefix));
    if (portal && !portalRoles[portal].includes(sessionUser.role)) {
      router.replace(roleHome[sessionUser.role]);
      return;
    }
    restoreSessionCookies();
    setUser(sessionUser);
  }, [pathname, router]);

  const nav = user ? navByRole[user.role] : [];

  return (
    <div className="min-h-screen bg-slate-100 lg:grid lg:grid-cols-[280px_1fr]">
      <aside className={`fixed inset-y-0 left-0 z-30 w-72 border-r border-slate-200 bg-ink text-white transition lg:static lg:block ${open ? "block" : "hidden"}`}>
        <div className="flex h-16 items-center border-b border-white/10 px-5">
          <div>
            <p className="text-lg font-bold">EduTrack</p>
            <p className="text-xs text-slate-300">School Management</p>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm ${active ? "bg-white text-ink" : "text-slate-200 hover:bg-white/10"}`}>
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-6">
          <button className="rounded-md p-2 lg:hidden" onClick={() => setOpen(!open)} aria-label="Toggle navigation">
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden w-full max-w-md items-center gap-2 rounded-md border border-slate-200 px-3 md:flex">
            <Search className="h-4 w-4 text-slate-400" />
            <input className="h-10 flex-1 outline-none" placeholder="Search students, invoices, results..." />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-semibold">{user?.name ?? "EduTrack User"}</p>
              <p className="text-xs text-slate-500">{user?.role ?? "Loading"}</p>
            </div>
            <button className="rounded-md border border-slate-200 p-2" onClick={logout} aria-label="Logout">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
