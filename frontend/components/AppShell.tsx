"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

const navItems = [
  { href: "/", label: "Dashboard", icon: "⌂" },
  { href: "/map", label: "Quarry Map", icon: "⌖" },
  { href: "/alerts", label: "Alerts & Notifications", icon: "!" },
  { href: "/history", label: "Monitoring History", icon: "◷" },
];

export default function AppShell({
  children,
  title,
  eyebrow,
  actions,
}: {
  children: ReactNode;
  title: string;
  eyebrow: string;
  actions?: ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] border-r border-white/10 bg-slate-900/80 lg:flex lg:flex-col">
        <div className="border-b border-white/10 px-6 py-6">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500 text-xl text-slate-950">◈</span>
            <span>
              <span className="block text-[15px] font-semibold tracking-tight text-white">QuarryWatch</span>
              <span className="mt-0.5 block text-[10px] uppercase tracking-[0.18em] text-slate-400">Field intelligence</span>
            </span>
          </Link>
        </div>

        <nav className="flex-1 px-3 py-6" aria-label="Primary navigation">
          <p className="px-3 pb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Workspace</p>
          <div className="space-y-1">
            {navItems.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-3 text-[13px] transition-colors ${
                    active
                      ? "bg-emerald-500/10 text-emerald-300"
                      : "text-slate-400 hover:bg-white/[0.03] hover:text-white"
                  }`}
                >
                  <span className={`flex h-6 w-6 items-center justify-center rounded-md border text-sm ${active ? "border-emerald-500/40 bg-emerald-500/10" : "border-white/10"}`}>{item.icon}</span>
                  {item.label}
                  {item.href === "/alerts" && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-amber-400" />}
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="m-4 rounded-xl border border-white/10 bg-slate-900/70 p-4">
          <div className="flex items-center gap-2 text-[11px] font-medium text-emerald-400"><span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" /> System operational</div>
          <p className="mt-2 text-[11px] leading-5 text-slate-400">Automated satellite monitoring is active. Next polling cycle in 45 seconds.</p>
        </div>
      </aside>

      <div className="lg:pl-[248px]">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/85 backdrop-blur-xl">
          <div className="flex min-h-[76px] items-center justify-between gap-4 px-5 sm:px-8 lg:px-10">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">{eyebrow}</p>
              <h1 className="mt-1 text-xl font-semibold tracking-tight text-white sm:text-2xl">{title}</h1>
            </div>
            <div className="flex flex-1 items-center justify-end gap-3">{actions}</div>
          </div>
          <div className="flex gap-1 overflow-x-auto border-t border-white/5 px-5 py-2 lg:hidden">
            {navItems.map((item) => <Link key={item.href} href={item.href} className={`whitespace-nowrap rounded-md px-3 py-2 text-xs ${pathname === item.href ? "bg-emerald-500/10 text-emerald-300" : "text-slate-400"}`}>{item.label}</Link>)}
          </div>
        </header>
        <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-6">{children}</main>
      </div>
    </div>
  );
}