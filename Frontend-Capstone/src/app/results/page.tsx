"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";

import AppShell from "@/components/AppShell";
import EmptyState from "@/components/EmptyState";
import MarkdownText from "@/components/MarkdownText";
import RequireAuth from "@/components/RequireAuth";
import ShapContributionGraph from "@/components/ShapContributionGraph";
import { formatCurrency, formatPercent } from "@/lib/format";
import { loadPrediction, loadProfile } from "@/lib/session";
import type { PatientProfileInput, PredictionResponse } from "@/lib/types";

export default function ResultsPage() {
  const hydrated = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const prediction: PredictionResponse | null = hydrated ? loadPrediction() : null;
  const profile: PatientProfileInput | null = hydrated ? loadProfile() : null;
  const usesShap = prediction ? prediction.explanation_method !== "heuristic" : false;

  return (
    <RequireAuth>
      <AppShell
        title="Assessment results"
        description="Review your premium estimate, risk summary, and the explainable insights that clarify what shaped the result."
        eyebrow="Step 3 of 4"
      >
        {!prediction ? (
          <EmptyState
            title="No prediction available"
            message="Run the assessment first so the frontend has a saved prediction to display."
          />
        ) : (
          <div className="space-y-6">
            <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="glass-panel rounded-[2rem] p-6 sm:p-8">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Premium estimate</p>
                <h2 className="mt-4 text-5xl font-semibold tracking-tight text-slate-950">
                  {formatCurrency(prediction.premium_estimate_monthly)}
                </h2>
                <div className="mt-6 grid gap-4 sm:grid-cols-3">
                  <div className="rounded-[1.5rem] bg-white/75 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Risk level</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-950">{prediction.risk_level}</p>
                  </div>
                  <div className="rounded-[1.5rem] bg-white/75 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Probability</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-950">{formatPercent(prediction.risk_probability)}</p>
                  </div>
                  <div className="rounded-[1.5rem] bg-white/75 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Confidence</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-950">{prediction.confidence_indicator}</p>
                  </div>
                </div>
                {profile && (
                  <div className="mt-6 rounded-[1.5rem] bg-slate-950 p-5 text-sm text-slate-200">
                    <p className="text-xs uppercase tracking-[0.32em] text-cyan-200">Saved profile snapshot</p>
                    <p className="mt-3 leading-7">
                      {profile.age} years old, {profile.region}, {profile.subscription_tier.toLowerCase()} tier, BMI {profile.bmi},
                      {profile.smoker_status ? " smoker" : " non-smoker"}.
                    </p>
                  </div>
                )}
              </div>

              <div className="glass-panel rounded-[2rem] p-6 sm:p-8">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">
                  {usesShap ? "Feature influence (SHAP values)" : "Feature influence"}
                </p>
                <p className="mt-4 text-sm leading-7 text-slate-600">
                  {usesShap
                    ? "SHAP values quantify how much each feature contributes to the final prediction. They provide a fair attribution view of the model output, showing which variables increase the projected risk and which variables pull it lower."
                    : "This view shows the model contribution signals currently available for the prediction. If the full ML explainability runtime is unavailable, the platform falls back to ranked feature contribution logic rather than SHAP values."}
                </p>
                <div className="mt-6">
                  <ShapContributionGraph
                    factors={prediction.top_factors}
                    explanationMethod={prediction.explanation_method}
                  />
                </div>
                <div className="mt-6 space-y-4">
                  {prediction.top_factors.map((factor) => (
                    <div key={`${factor.feature_name}-${factor.direction}`} className="rounded-[1.5rem] bg-white/75 p-5">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 className="text-xl font-semibold text-slate-950">{factor.feature_name.replaceAll("_", " ")}</h3>
                        <span className="rounded-full bg-slate-950 px-3 py-1 text-xs uppercase tracking-[0.2em] text-white">
                          {factor.direction}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-slate-600">{factor.plain_language}</p>
                      <div className="mt-4">
                        <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-slate-500">
                          <span>Contribution value</span>
                          <span>{factor.value.toFixed(4)}</span>
                        </div>
                        <div className="h-3 rounded-full bg-slate-100">
                          <div
                            className={`h-3 rounded-full ${factor.direction === "decreases risk" ? "bg-emerald-500" : "bg-rose-500"}`}
                            style={{ width: `${Math.min(Math.max(Math.abs(factor.value) * 140, 12), 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
              <article className="glass-panel rounded-[2rem] p-6 sm:p-8">
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Narrative explanation</p>
                <div className="mt-6 rounded-[1.75rem] bg-white/75 p-6">
                  <MarkdownText content={prediction.explanation_markdown} />
                </div>
                <div className="mt-6 rounded-[1.75rem] bg-slate-950 p-5 text-sm leading-7 text-slate-200">
                  <p className="text-xs uppercase tracking-[0.32em] text-cyan-200">Clinical insight and model logic</p>
                  <p className="mt-3">
                    {usesShap
                      ? "Explainable AI is used here to make the model decision process transparent and interpretable. The risk level summarizes the predicted category, the probability expresses the estimated likelihood of that outcome, and the SHAP values show how each feature contributed to the final result."
                      : "The risk level summarizes the predicted category and the probability expresses the estimated likelihood of that outcome. This result is currently using fallback feature contribution logic, so the ranking is still useful for interpretation but should not be described as SHAP."}
                  </p>
                </div>
              </article>
              <aside className="space-y-6">
                <div className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Recommended next step</p>
                  <div className="mt-5 grid gap-3">
                    <Link href="/forecast" className="rounded-full bg-slate-950 px-5 py-3 text-center text-sm font-medium text-white">
                      View 36-month premium outlook
                    </Link>
                    <Link href="/simulator" className="rounded-full border border-slate-200 bg-white px-5 py-3 text-center text-sm font-medium text-slate-700">
                      Test a lifestyle change scenario
                    </Link>
                    <Link href="/plans" className="rounded-full border border-slate-200 bg-white px-5 py-3 text-center text-sm font-medium text-slate-700">
                      Check plan recommendation status
                    </Link>
                  </div>
                </div>
                <div className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Interpretation summary</p>
                  <div className="mt-4 text-sm leading-7 text-slate-600">
                    <p>Primary driver: <span className="font-medium text-slate-950">{prediction.top_driver}</span></p>
                    <p>Result status: <span className="font-medium text-slate-950">{prediction.status}</span></p>
                    <p>Saved profile version: <span className="font-medium text-slate-950">{prediction.profile_version ?? "Not persisted"}</span></p>
                  </div>
                </div>
              </aside>
            </section>
          </div>
        )}
      </AppShell>
    </RequireAuth>
  );
}
