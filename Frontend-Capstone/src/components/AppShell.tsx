"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useSession } from "@/components/providers/SessionProvider";
import { logoutRequest } from "@/lib/api";
import { clearAppData } from "@/lib/session";

type AppShellProps = {
  title: string;
  description: string;
  eyebrow?: string;
  children: React.ReactNode;
};

const baseLinks = [
  { href: "/assessment", label: "Assessment" },
  { href: "/results", label: "Results" },
  { href: "/forecast", label: "Forecast" },
  { href: "/simulator", label: "Simulator" },
  { href: "/plans", label: "Plans" },
];

export default function AppShell({
  title,
  description,
  eyebrow = "Insurance Intelligence Workspace",
  children,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { session, setSession } = useSession();

  const links =
    session?.user.role === "admin"
      ? [...baseLinks, { href: "/admin", label: "Admin" }]
      : baseLinks;

  const handleLogout = async () => {
    const token = session?.accessToken;
    setSession(null);
    clearAppData();
    await logoutRequest(token);
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(180,225,255,0.35),_transparent_32%),linear-gradient(180deg,_#f4efe1_0%,_#fbf9f2_48%,_#eef5ff_100%)] text-slate-900">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="glass-panel mb-8 flex flex-col gap-6 rounded-[2rem] px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Link href="/" className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">
              Medisight AI
            </Link>
            <div className="mt-3">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-700">{eyebrow}</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">{title}</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">{description}</p>
            </div>
          </div>

          <div className="flex flex-col gap-4 lg:items-end">
            <nav className="flex flex-wrap gap-2">
              {links.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-full px-4 py-2 text-sm transition ${
                      active
                        ? "bg-slate-950 text-white shadow-lg"
                        : "bg-white/70 text-slate-600 hover:bg-white hover:text-slate-950"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-white/70 px-4 py-2 text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{session?.user.tenant_name}</span>
                <span className="mx-2 text-slate-300">/</span>
                <span className="text-xs uppercase tracking-[0.2em]">{session?.user.role}</span>
              </div>
              <button
                onClick={handleLogout}
                className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              >
                Log out
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
