import { useQuery, useQueryClient } from "@tanstack/react-query";
import { HeartHandshake, ListChecks, LogOut, Menu, Repeat2, ShieldCheck, Shuffle, Star } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Navigate, Outlet } from "react-router-dom";
import { api } from "../lib/api";
import { clearToken, getToken } from "../lib/auth";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: Star },
  { to: "/haves", label: "Have", icon: ListChecks },
  { to: "/wants", label: "Want", icon: HeartHandshake },
  { to: "/matches/direct", label: "1:1", icon: Repeat2 },
  { to: "/matches/three-way", label: "3-way", icon: Shuffle },
  { to: "/admin/pending-photocards", label: "검토", icon: ShieldCheck }
];

export function AppLayout() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const token = getToken();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: Boolean(token) });

  if (!token) return <Navigate to="/login" replace />;

  function logout() {
    clearToken();
    queryClient.clear();
    window.location.href = "/login";
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link to="/dashboard" className="flex items-center gap-2 font-semibold text-slate-950">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-950 text-sm text-white">
              PL
            </span>
            <span>poca-loop</span>
          </Link>
          <div className="hidden items-center gap-3 md:flex">
            <span className="text-sm text-slate-500">@{me.data?.username ?? "..."}</span>
            <Button variant="secondary" onClick={logout}>
              <LogOut size={16} />
              Logout
            </Button>
          </div>
          <Button variant="ghost" className="md:hidden" onClick={() => setOpen((value) => !value)}>
            <Menu size={20} />
          </Button>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-4 px-4 py-4 md:grid-cols-[220px_1fr]">
        <aside className={cn("md:block", open ? "block" : "hidden")}>
          <nav className="grid gap-1 rounded-lg border border-slate-200 bg-white p-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-600",
                    isActive && "bg-slate-950 text-white"
                  )
                }
              >
                <item.icon size={17} />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
