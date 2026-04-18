"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import RequireAuth from "@/components/RequireAuth";
import { apiRequest } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { AdminDashboardResponse, AdminMetricsResponse, TrainingExportResponse } from "@/lib/types";

export default function AdminPage() {
  const [dashboard, setDashboard] = useState<AdminDashboardResponse | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsResponse | null>(null);
  const [exportResult, setExportResult] = useState<TrainingExportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [dashboardResponse, metricsResponse] = await Promise.all([
          apiRequest<AdminDashboardResponse>("/admin/dashboard"),
          apiRequest<AdminMetricsResponse>("/admin/metrics"),
        ]);
        if (active) {
          setDashboard(dashboardResponse);
          setMetrics(metricsResponse);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load admin metrics.");
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

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    try {
      const response = await apiRequest<TrainingExportResponse>("/admin/training-data/export", {
        method: "POST",
      });
      setExportResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to export training data.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <RequireAuth role="admin">
      <AppShell
        title="Admin analytics"
        description="Monitor platform activity, user adoption, and reporting readiness from the administrative dashboard."
        eyebrow="Administrative dashboard"
      >
        {isLoading ? (
          <LoadingState message="Loading admin telemetry..." />
        ) : error && !dashboard ? (
          <ErrorState title="Admin dashboard unavailable" message={error} />
        ) : dashboard && metrics ? (
          <div className="space-y-6">
            <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <article className="glass-panel rounded-[2rem] p-6">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Total users</p>
                <h2 className="mt-3 text-4xl font-semibold text-slate-950">{formatNumber(dashboard.accounts.accounts_created)}</h2>
              </article>
              <article className="glass-panel rounded-[2rem] p-6">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Active users</p>
                <h2 className="mt-3 text-4xl font-semibold text-slate-950">{formatNumber(metrics.active_users)}</h2>
              </article>
              <article className="glass-panel rounded-[2rem] p-6">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">API health</p>
                <h2 className="mt-3 text-4xl font-semibold text-slate-950">{formatNumber(metrics.avg_response_time_ms)} ms</h2>
              </article>
              <article className="glass-panel rounded-[2rem] p-6">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Error rate</p>
                <h2 className="mt-3 text-4xl font-semibold text-slate-950">{formatNumber(metrics.error_rate, 2)}%</h2>
              </article>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <article className="glass-panel rounded-[2rem] p-6 sm:p-8">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Feature usage</p>
                <div className="mt-6 space-y-4">
                  {dashboard.workflow_split.map((item) => (
                    <div key={item.feature_type} className="rounded-[1.5rem] bg-white/75 p-5">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xl font-semibold text-slate-950">{item.feature_type}</h3>
                        <span className="text-sm text-slate-500">{formatNumber(item.count)} events</span>
                      </div>
                      <div className="mt-4 h-3 rounded-full bg-slate-100">
                        <div className="h-3 rounded-full bg-cyan-600" style={{ width: `${item.percentage}%` }} />
                      </div>
                      <p className="mt-3 text-sm text-slate-600">{formatNumber(item.percentage, 2)}% of overall platform activity</p>
                    </div>
                  ))}
                </div>
              </article>

              <aside className="space-y-6">
                <div className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Usage funnel</p>
                  <div className="mt-5 space-y-3 text-sm leading-7 text-slate-600">
                    <p>Prediction views: <span className="font-medium text-slate-950">{dashboard.usage_funnel.prediction_views}</span></p>
                    <p>Forecast views: <span className="font-medium text-slate-950">{dashboard.usage_funnel.forecast_views}</span></p>
                    <p>Recommendation views: <span className="font-medium text-slate-950">{dashboard.usage_funnel.recommendation_views}</span></p>
                  </div>
                </div>
                <div className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Sanitized export</p>
                  <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className="mt-5 w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {isExporting ? "Exporting..." : "Export sanitized training data"}
                  </button>
                  {exportResult && (
                    <div className="mt-5 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                      <p>Records prepared: {exportResult.row_count}</p>
                      <p className="break-all">Export file: {exportResult.output_path}</p>
                    </div>
                  )}
                  {error && (
                    <div className="mt-5 rounded-[1.5rem] border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                      {error}
                    </div>
                  )}
                </div>
              </aside>
            </section>
          </div>
        ) : null}
      </AppShell>
    </RequireAuth>
  );
}
