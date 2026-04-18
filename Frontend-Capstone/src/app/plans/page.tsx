"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import RequireAuth from "@/components/RequireAuth";
import { apiRequest } from "@/lib/api";
import { loadProfile } from "@/lib/session";
import type { ComingSoonResponse } from "@/lib/types";

export default function PlansPage() {
  const [response, setResponse] = useState<ComingSoonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const result = await apiRequest<ComingSoonResponse>("/plans/recommend", {
          method: "POST",
        });
        if (active) {
          setResponse(result);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "Unable to reach the plan finder.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    load();
    return () => {
      active = false;
    };
  }, []);

  const profile = loadProfile();

  return (
    <RequireAuth>
      <AppShell
        title="Plan finder status"
        description="Review the current availability of plan recommendations and continue with the personalized guidance already available in your assessment journey."
        eyebrow="Plan guidance"
      >
        {isLoading ? (
          <LoadingState message="Preparing your plan guidance..." />
        ) : error ? (
          <ErrorState title="Plan finder unavailable" message={error} />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <section className="glass-panel rounded-[2rem] p-6 sm:p-8">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Recommendation availability</p>
              <h2 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">Personalized plan recommendations are being prepared.</h2>
              <p className="mt-5 text-base leading-8 text-slate-600">
                {response?.message || "Your assessment, forecast, and simulation results are already available to support coverage planning while recommendation matching is finalized."}
              </p>
              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                <div className="rounded-[1.5rem] bg-white/75 p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Current status</p>
                  <p className="mt-2 text-2xl font-semibold capitalize text-slate-950">{(response?.status || "unavailable").replaceAll("_", " ")}</p>
                </div>
                <div className="rounded-[1.5rem] bg-white/75 p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Service area</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-950">Plan guidance</p>
                </div>
              </div>
            </section>

            <aside className="space-y-6">
              <div className="glass-panel rounded-[2rem] p-6">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Continue your coverage review</p>
                <div className="mt-5 grid gap-3">
                  <Link href="/results" className="rounded-full bg-slate-950 px-5 py-3 text-center text-sm font-medium text-white">
                    Review assessment results
                  </Link>
                  <Link href="/forecast" className="rounded-full border border-slate-200 bg-white px-5 py-3 text-center text-sm font-medium text-slate-700">
                    View premium forecast
                  </Link>
                  <Link href="/simulator" className="rounded-full border border-slate-200 bg-white px-5 py-3 text-center text-sm font-medium text-slate-700">
                    Explore scenario changes
                  </Link>
                </div>
              </div>
              {profile && (
                <div className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Last saved profile</p>
                  <p className="mt-4 text-sm leading-7 text-slate-600">
                    {profile.region}, {profile.subscription_tier} tier, risk baseline {profile.base_risk_score}.
                  </p>
                </div>
              )}
            </aside>
          </div>
        )}
      </AppShell>
    </RequireAuth>
  );
}
