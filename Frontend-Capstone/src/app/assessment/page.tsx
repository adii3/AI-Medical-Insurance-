"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import AppShell from "@/components/AppShell";
import RequireAuth from "@/components/RequireAuth";
import LoadingState from "@/components/LoadingState";
import { useSession } from "@/components/providers/SessionProvider";
import { apiRequest } from "@/lib/api";
import { DEFAULT_PROFILE, REGIONS, SEXES, SUBSCRIPTION_TIERS } from "@/lib/constants";
import { loadProfile, savePrediction, saveProfile } from "@/lib/session";
import type { PatientProfileInput, PredictionResponse, ProfileUpsertResponse } from "@/lib/types";

function withTenant(profile: PatientProfileInput, tenantName: string): PatientProfileInput {
  return {
    ...profile,
    tenant_company: profile.tenant_company || tenantName,
  };
}

export default function AssessmentPage() {
  const router = useRouter();
  const { session } = useSession();
  const [formData, setFormData] = useState<PatientProfileInput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    const hydrate = async () => {
      if (!session) {
        return;
      }

      const fallback = withTenant(loadProfile() || DEFAULT_PROFILE, session.user.tenant_name);

      try {
        const response = await apiRequest<ProfileUpsertResponse>("/me/profile");
        if (!active) {
          return;
        }
        const nextProfile = withTenant(response.profile, session.user.tenant_name);
        setFormData(nextProfile);
        saveProfile(nextProfile);
      } catch {
        if (!active) {
          return;
        }
        setFormData(fallback);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    hydrate();
    return () => {
      active = false;
    };
  }, [session]);

  const updateField = <K extends keyof PatientProfileInput>(key: K, value: PatientProfileInput[K]) => {
    setFormData((current) => (current ? { ...current, [key]: value } : current));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!formData) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const profile = withTenant(formData, session?.user.tenant_name || "");
      const prediction = await apiRequest<PredictionResponse>("/predict", {
        method: "POST",
        body: {
          profile,
          persist_profile: true,
        },
      });
      saveProfile(profile);
      savePrediction(prediction);
      router.push("/results");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to run prediction.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || !formData) {
    return (
      <RequireAuth>
        <AppShell
          title="Customer assessment"
          description="Collect the profile inputs required by the prediction model."
          eyebrow="Step 2 of 4"
        >
          <LoadingState message="Loading your latest profile..." />
        </AppShell>
      </RequireAuth>
    );
  }

  return (
    <RequireAuth>
      <AppShell
        title="Customer assessment"
        description="Complete the profile questions used to generate your premium estimate, risk outlook, and explainable assessment summary."
        eyebrow="Step 2 of 4"
      >
        <form className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]" onSubmit={handleSubmit}>
          <section className="glass-panel rounded-[2rem] p-6 sm:p-8">
            <div className="grid gap-5 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Age</span>
                <input
                  type="number"
                  min={18}
                  max={90}
                  value={formData.age}
                  onChange={(event) => updateField("age", Number(event.target.value))}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">BMI</span>
                <input
                  type="number"
                  min={15}
                  max={55}
                  step="0.1"
                  value={formData.bmi}
                  onChange={(event) => updateField("bmi", Number(event.target.value))}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Smoking status</span>
                <select
                  value={String(formData.smoker_status)}
                  onChange={(event) => updateField("smoker_status", event.target.value === "true")}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                >
                  <option value="false">Non-smoker</option>
                  <option value="true">Smoker</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Dependents</span>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={formData.dependents}
                  onChange={(event) => updateField("dependents", Number(event.target.value))}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Province</span>
                <select
                  value={formData.region}
                  onChange={(event) => updateField("region", event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                >
                  {REGIONS.map((region) => (
                    <option key={region} value={region}>
                      {region}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Sex</span>
                <select
                  value={formData.sex}
                  onChange={(event) => updateField("sex", event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                >
                  {SEXES.map((sex) => (
                    <option key={sex} value={sex}>
                      {sex}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Recent hospitalizations</span>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={formData.recent_hospitalizations}
                  onChange={(event) => updateField("recent_hospitalizations", Number(event.target.value))}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Subscription tier</span>
                <select
                  value={formData.subscription_tier}
                  onChange={(event) => updateField("subscription_tier", event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                >
                  {SUBSCRIPTION_TIERS.map((tier) => (
                    <option key={tier} value={tier}>
                      {tier}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block md:col-span-2">
                <span className="mb-2 block text-sm font-medium text-slate-700">Base risk score</span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={formData.base_risk_score}
                  onChange={(event) => updateField("base_risk_score", Number(event.target.value))}
                  className="w-full"
                />
                <div className="mt-2 flex justify-between text-xs uppercase tracking-[0.2em] text-slate-500">
                  <span>0</span>
                  <span>{formData.base_risk_score}</span>
                  <span>100</span>
                </div>
              </label>
            </div>
          </section>

          <aside className="space-y-6">
            <section className="glass-panel rounded-[2rem] p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Assessment context</p>
              <div className="mt-5 space-y-3 text-sm text-slate-600">
                <p>Tenant: <span className="font-medium text-slate-950">{session?.user.tenant_name}</span></p>
                <p>Assessment mode: <span className="font-medium text-slate-950">Personalized premium evaluation</span></p>
                <p>Assessment output: <span className="font-medium text-slate-950">Premium estimate, risk summary, feature impact view, and profile snapshot</span></p>
              </div>
            </section>

            <section className="glass-panel rounded-[2rem] p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Explainable AI guide</p>
              <div className="mt-5 space-y-4 text-sm leading-7 text-slate-600">
                <p>
                  Explainable AI, or XAI, refers to the processes and methods that allow users to understand and trust
                  the outputs produced by machine learning models. In this assessment, XAI is used to make the premium
                  decision process more transparent and interpretable.
                </p>
                <p>
                  <span className="font-medium text-slate-950">SHAP</span>, or SHapley Additive exPlanations, is a
                  feature-attribution method that fairly assigns the contribution of each variable to the final
                  prediction, treating the prediction as a cooperative game in which each feature acts like a player.
                </p>
                <p>
                  <span className="font-medium text-slate-950">Risk probability</span> reflects the model-estimated
                  likelihood that the profile belongs to a higher-cost risk segment.
                </p>
                <p>
                  <span className="font-medium text-slate-950">Top factors</span> identify the variables with the
                  strongest SHAP contribution to the result, while the confidence indicator reflects how strongly the
                  model distinguishes this profile from a borderline case.
                </p>
                <div className="rounded-[1.5rem] bg-white/75 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">What you will see after assessment</p>
                  <div className="mt-4 space-y-3">
                    <div>
                      <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                        <span>Smoking Status</span>
                        <span>Higher positive SHAP value</span>
                      </div>
                      <div className="h-3 rounded-full bg-slate-100">
                        <div className="h-3 w-[82%] rounded-full bg-rose-500" />
                      </div>
                    </div>
                    <div>
                      <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                        <span>BMI</span>
                        <span>Moderate SHAP value</span>
                      </div>
                      <div className="h-3 rounded-full bg-slate-100">
                        <div className="h-3 w-[58%] rounded-full bg-amber-500" />
                      </div>
                    </div>
                    <div>
                      <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                        <span>Region or Tier</span>
                        <span>Supporting SHAP value</span>
                      </div>
                      <div className="h-3 rounded-full bg-slate-100">
                        <div className="h-3 w-[34%] rounded-full bg-cyan-600" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <label className="glass-panel flex gap-4 rounded-[2rem] p-6">
              <input
                type="checkbox"
                checked={formData.consent_to_model_improvement}
                onChange={(event) => updateField("consent_to_model_improvement", event.target.checked)}
                className="mt-1 h-5 w-5 rounded border-slate-300"
              />
              <span className="text-sm leading-7 text-slate-700">
                Allow this profile to contribute anonymously to future product improvement and insight quality.
              </span>
            </label>

            {error && (
              <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isSubmitting ? "Preparing your assessment..." : "Generate assessment results"}
            </button>
          </aside>
        </form>
      </AppShell>
    </RequireAuth>
  );
}
