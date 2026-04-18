"use client";

import Link from "next/link";

import { useSession } from "@/components/providers/SessionProvider";
import { getAuthenticatedHome } from "@/lib/constants";

const featureCards = [
  {
    title: "Trusted digital onboarding",
    text: "Every journey starts with secure sign-up, MFA verification, and consent-aware onboarding so pricing analysis begins on a compliant foundation.",
  },
  {
    title: "Explainable premium intelligence",
    text: "Instead of a black-box quote, the platform explains the drivers behind the estimate with feature impact signals, risk context, and plain-language reasoning.",
  },
  {
    title: "Scenario and trend modeling",
    text: "Users can move from a single estimate to long-term forecasting and what-if analysis, turning premium pricing into an actionable planning conversation.",
  },
  {
    title: "Operational visibility",
    text: "Operations teams can track adoption, service health, and reporting readiness from a dedicated administrative workspace.",
  },
];

export default function LandingPage() {
  const { session, hydrated } = useSession();
  const primaryHref = hydrated ? getAuthenticatedHome(session) : "/login";
  const primaryLabel = session ? "Open dashboard" : "Start your assessment";

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_32%),radial-gradient(circle_at_bottom_right,_rgba(15,23,42,0.16),_transparent_28%),linear-gradient(180deg,_#f7f2e6_0%,_#fbfaf5_48%,_#eef4ff_100%)]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="glass-panel flex items-center justify-between rounded-[2rem] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-700">Medisight AI</p>
            <p className="mt-2 text-sm text-slate-600">Explainable medical insurance intelligence platform</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/login"
              className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="rounded-full bg-slate-950 px-5 py-3 text-sm font-medium text-white shadow-lg transition hover:bg-slate-800"
            >
              Create account
            </Link>
          </div>
        </header>

        <main className="flex flex-1 flex-col justify-center py-12">
          <section className="grid items-center gap-10 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <div className="inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">
                Explainable AI for premium decisions
              </div>
              <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight text-slate-950 sm:text-6xl lg:text-7xl">
                Predict with clarity, understand risk, and plan coverage with confidence.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
                Medisight AI transforms medical insurance assessment into a guided decision experience, combining trusted
                onboarding, explainable premium analysis, scenario planning, and long-range cost forecasting.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <Link
                  href={primaryHref}
                  className="rounded-full bg-slate-950 px-6 py-4 text-sm font-medium text-white shadow-xl transition hover:-translate-y-0.5 hover:bg-slate-800"
                >
                  {primaryLabel}
                </Link>
                <Link
                  href="/plans"
                  className="rounded-full border border-slate-200 bg-white px-6 py-4 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  Explore the experience
                </Link>
              </div>
            </div>

            <div className="glass-panel dash-grid rounded-[2.5rem] p-8">
              <div className="rounded-[2rem] bg-slate-950 p-6 text-white shadow-2xl">
                <p className="text-xs uppercase tracking-[0.32em] text-cyan-200">What the platform delivers</p>
                <div className="mt-6 space-y-4">
                  <div className="rounded-[1.5rem] bg-white/10 p-4">
                    <p className="text-sm text-slate-300">Member experience</p>
                    <p className="mt-2 text-xl font-semibold">Secure onboarding, personalized assessment, and transparent results</p>
                  </div>
                  <div className="rounded-[1.5rem] bg-white/10 p-4">
                    <p className="text-sm text-slate-300">Decision support</p>
                    <p className="mt-2 text-xl font-semibold">Premium prediction, explainable insights, what-if analysis, and future forecasting</p>
                  </div>
                  <div className="rounded-[1.5rem] bg-cyan-300/15 p-4">
                    <p className="text-sm text-cyan-100">Administrative oversight</p>
                    <p className="mt-2 text-xl font-semibold">Operational metrics, platform usage, and export-ready reporting in one place</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="mt-16 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {featureCards.map((card) => (
              <article key={card.title} className="glass-panel rounded-[2rem] p-6">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Platform pillar</p>
                <h2 className="mt-4 text-2xl font-semibold tracking-tight text-slate-950">{card.title}</h2>
                <p className="mt-4 text-sm leading-7 text-slate-600">{card.text}</p>
              </article>
            ))}
          </section>
        </main>
      </div>
    </div>
  );
}
