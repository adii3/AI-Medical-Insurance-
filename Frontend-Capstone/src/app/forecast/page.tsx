"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import RequireAuth from "@/components/RequireAuth";
import { apiRequest } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { loadProfile } from "@/lib/session";
import type { ForecastResponse, PatientProfileInput } from "@/lib/types";

export default function ForecastPage() {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const fetchForecast = async () => {
      const profile = loadProfile();
      if (!profile) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiRequest<ForecastResponse>("/forecast", {
          method: "POST",
          body: {
            profile,
            persist_profile: false,
          },
        });
        if (active) {
          setForecast(response);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load forecast.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    fetchForecast();
    return () => {
      active = false;
    };
  }, []);

  const profile = loadProfile() as PatientProfileInput | null;

  return (
    <RequireAuth>
      <AppShell
        title="36-month premium forecast"
        description="See how your current assessment may translate into premium movement over time through a long-range cost outlook."
        eyebrow="Step 4 of 4"
      >
        {isLoading ? (
          <LoadingState message="Calculating long-range premium movement..." />
        ) : error ? (
          <ErrorState title="Forecast unavailable" message={error} />
        ) : !forecast ? (
          <EmptyState
            title="No profile available"
            message="Save an assessment first so the forecast endpoint has a valid customer profile to project."
          />
        ) : (
          <div className="space-y-6">
            <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <article className="glass-panel rounded-[2rem] p-6 sm:p-8">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Projection overview</p>
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-[1.5rem] bg-white/75 p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Current estimate</p>
                    <p className="mt-2 text-4xl font-semibold text-slate-950">{formatCurrency(forecast.current_premium_estimate)}</p>
                  </div>
                  <div className="rounded-[1.5rem] bg-white/75 p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Projection horizon</p>
                    <p className="mt-2 text-4xl font-semibold text-slate-950">{forecast.months.length} months</p>
                  </div>
                </div>

                <div className="mt-8 rounded-[1.75rem] bg-white/75 p-5">
                  <div className="flex justify-between text-xs uppercase tracking-[0.2em] text-slate-500">
                    <span>Historical + forecast path</span>
                    <span>{forecast.months[0]} to {forecast.months[forecast.months.length - 1]}</span>
                  </div>
                  <svg viewBox="0 0 900 280" className="mt-6 w-full">
                    {(() => {
                      const combined = [...forecast.historical_premiums, ...forecast.forecast_premiums];
                      const max = Math.max(...combined);
                      const min = Math.min(...combined);
                      const range = Math.max(max - min, 1);
                      const points = combined
                        .map((value, index) => {
                          const x = (index / Math.max(combined.length - 1, 1)) * 860 + 20;
                          const y = 240 - ((value - min) / range) * 180;
                          return `${x},${y}`;
                        })
                        .join(" ");
                      return (
                        <>
                          <polyline fill="none" stroke="#0891b2" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" points={points} />
                          {combined.map((value, index) => {
                            if (index % 6 !== 0 && index !== combined.length - 1) {
                              return null;
                            }
                            const x = (index / Math.max(combined.length - 1, 1)) * 860 + 20;
                            const y = 240 - ((value - min) / range) * 180;
                            return (
                              <g key={`${value}-${index}`}>
                                <circle cx={x} cy={y} r="6" fill="#ffffff" stroke="#0f172a" strokeWidth="2" />
                                <text x={x} y={y - 14} textAnchor="middle" className="fill-slate-700 text-[12px]">
                                  {Math.round(value)}
                                </text>
                              </g>
                            );
                          })}
                        </>
                      );
                    })()}
                  </svg>
                </div>
              </article>

              <aside className="space-y-6">
                <div className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Trend narrative</p>
                  <p className="mt-5 text-sm leading-7 text-slate-600">{forecast.trend_summary}</p>
                </div>
                {profile && (
                  <div className="glass-panel rounded-[2rem] p-6">
                    <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Assessment profile</p>
                    <div className="mt-4 text-sm leading-7 text-slate-600">
                      <p>{profile.region}</p>
                      <p>{profile.subscription_tier} tier</p>
                      <p>{profile.smoker_status ? "Smoker" : "Non-smoker"}</p>
                    </div>
                  </div>
                )}
              </aside>
            </section>
          </div>
        )}
      </AppShell>
    </RequireAuth>
  );
}
