"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import MarkdownText from "@/components/MarkdownText";
import RequireAuth from "@/components/RequireAuth";
import { apiRequest } from "@/lib/api";
import { REGIONS, SUBSCRIPTION_TIERS } from "@/lib/constants";
import { formatCurrency, formatPercent } from "@/lib/format";
import { loadPrediction, loadProfile, savePrediction } from "@/lib/session";
import type { PatientProfileInput, PredictionResponse } from "@/lib/types";

type SimulatorState = {
  bmi: number;
  smoker_status: boolean;
  dependents: number;
  region: string;
  recent_hospitalizations: number;
  base_risk_score: number;
  subscription_tier: string;
};

function getInitialState(profile: PatientProfileInput): SimulatorState {
  return {
    bmi: profile.bmi,
    smoker_status: profile.smoker_status,
    dependents: profile.dependents,
    region: profile.region,
    recent_hospitalizations: profile.recent_hospitalizations,
    base_risk_score: profile.base_risk_score,
    subscription_tier: profile.subscription_tier,
  };
}

export default function SimulatorPage() {
  const [profile, setProfile] = useState<PatientProfileInput | null>(null);
  const [baseline, setBaseline] = useState<PredictionResponse | null>(null);
  const [simulation, setSimulation] = useState<PredictionResponse | null>(null);
  const [controls, setControls] = useState<SimulatorState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    let active = true;

    const hydrate = async () => {
      const savedProfile = loadProfile();
      if (!savedProfile) {
        setIsLoading(false);
        return;
      }

      setProfile(savedProfile);
      setControls(getInitialState(savedProfile));

      const savedPrediction = loadPrediction();
      if (savedPrediction) {
        setBaseline(savedPrediction);
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiRequest<PredictionResponse>("/predict", {
          method: "POST",
          body: {
            profile: savedProfile,
            persist_profile: false,
          },
        });
        if (active) {
          setBaseline(response);
          savePrediction(response);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "Unable to build baseline prediction.");
        }
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
  }, []);

  const runSimulation = async () => {
    if (!profile || !controls) {
      return;
    }

    setError(null);
    setIsRunning(true);

    try {
      const response = await apiRequest<PredictionResponse>("/predict/what-if", {
        method: "POST",
        body: {
          overrides: controls,
        },
      });
      setSimulation(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to run simulation.");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <RequireAuth>
      <AppShell
        title="What-if simulator"
        description="Adjust key profile variables to explore how health, lifestyle, and coverage changes may alter your premium outlook."
        eyebrow="Scenario testing"
      >
        {isLoading ? (
          <LoadingState message="Preparing baseline prediction..." />
        ) : error && !profile ? (
          <ErrorState title="Simulator unavailable" message={error} />
        ) : !profile || !controls || !baseline ? (
          <EmptyState
            title="No saved assessment"
            message="Complete the assessment first so the simulator has a stored profile and baseline prediction."
          />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <aside className="glass-panel rounded-[2rem] p-6 sm:p-8">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Scenario controls</p>
              <div className="mt-6 space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">BMI</span>
                  <input
                    type="number"
                    min={15}
                    max={55}
                    step="0.1"
                    value={controls.bmi}
                    onChange={(event) => setControls((current) => current ? { ...current, bmi: Number(event.target.value) } : current)}
                    className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Smoking status</span>
                  <select
                    value={String(controls.smoker_status)}
                    onChange={(event) => setControls((current) => current ? { ...current, smoker_status: event.target.value === "true" } : current)}
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
                    value={controls.dependents}
                    onChange={(event) => setControls((current) => current ? { ...current, dependents: Number(event.target.value) } : current)}
                    className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Province</span>
                  <select
                    value={controls.region}
                    onChange={(event) => setControls((current) => current ? { ...current, region: event.target.value } : current)}
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
                  <span className="mb-2 block text-sm font-medium text-slate-700">Recent hospitalizations</span>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    value={controls.recent_hospitalizations}
                    onChange={(event) => setControls((current) => current ? { ...current, recent_hospitalizations: Number(event.target.value) } : current)}
                    className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Base risk score</span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={controls.base_risk_score}
                    onChange={(event) => setControls((current) => current ? { ...current, base_risk_score: Number(event.target.value) } : current)}
                    className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">Subscription tier</span>
                  <select
                    value={controls.subscription_tier}
                    onChange={(event) => setControls((current) => current ? { ...current, subscription_tier: event.target.value } : current)}
                    className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                  >
                    {SUBSCRIPTION_TIERS.map((tier) => (
                      <option key={tier} value={tier}>
                        {tier}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {error && (
                <div className="mt-5 rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
                  {error}
                </div>
              )}

              <button
                onClick={runSimulation}
                disabled={isRunning}
                className="mt-6 w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isRunning ? "Running scenario..." : "Run what-if scenario"}
              </button>
            </aside>

            <section className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <article className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Current outlook</p>
                  <h2 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">{formatCurrency(baseline.premium_estimate_monthly)}</h2>
                  <p className="mt-4 text-sm leading-7 text-slate-600">
                    {baseline.risk_level} risk at {formatPercent(baseline.risk_probability)} probability.
                  </p>
                </article>
                <article className="glass-panel rounded-[2rem] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Updated outlook</p>
                  <h2 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">
                    {simulation ? formatCurrency(simulation.premium_estimate_monthly) : "Pending"}
                  </h2>
                  <p className="mt-4 text-sm leading-7 text-slate-600">
                    {simulation
                      ? `${simulation.risk_level} risk at ${formatPercent(simulation.risk_probability)} probability.`
                      : "Run a simulation to compare the adjusted premium and risk profile."}
                  </p>
                </article>
              </div>

              {simulation && (
                <>
                  <div className="glass-panel rounded-[2rem] p-6">
                    <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Premium delta</p>
                    <p className="mt-4 text-3xl font-semibold text-slate-950">
                      {formatCurrency(simulation.premium_estimate_monthly - baseline.premium_estimate_monthly)}
                    </p>
                  </div>
                  <div className="glass-panel rounded-[2rem] p-6">
                    <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">Scenario narrative</p>
                    <div className="mt-5 rounded-[1.5rem] bg-white/75 p-5">
                      <MarkdownText content={simulation.explanation_markdown} />
                    </div>
                  </div>
                </>
              )}
            </section>
          </div>
        )}
      </AppShell>
    </RequireAuth>
  );
}
