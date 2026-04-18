"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import AppShell from "@/components/AppShell";
import RequireAuth from "@/components/RequireAuth";
import { useSession } from "@/components/providers/SessionProvider";
import { apiRequest } from "@/lib/api";
import { getAuthenticatedHome } from "@/lib/constants";
import type { OnboardingResponse } from "@/lib/types";

export default function OnboardingPage() {
  const router = useRouter();
  const { session, updateUser } = useSession();
  const [state, setState] = useState({
    consent_accepted: false,
    platform_purpose_seen: false,
    data_use_summary_seen: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (session?.user.onboarded) {
      router.replace(getAuthenticatedHome(session));
    }
  }, [router, session]);

  const handleSubmit = async () => {
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await apiRequest<OnboardingResponse>("/me/onboarding", {
        method: "POST",
        body: {
          consent_version: "2026-03",
          ...state,
        },
      });

      if (session) {
        updateUser({ ...session.user, onboarded: response.onboarded });
      }
      router.push("/assessment");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save onboarding.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <RequireAuth>
      <AppShell
        title="Consent and onboarding"
        description="Review how the platform supports your assessment journey and confirm the consent steps required before continuing."
        eyebrow="Step 1 of 4"
      >
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="glass-panel rounded-[2rem] p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-700">What this step covers</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">Begin your assessment with clarity and consent.</h2>
            <ul className="mt-6 space-y-4 text-sm leading-7 text-slate-600">
              <li>This step explains how Medisight AI supports premium prediction and risk understanding.</li>
              <li>You review the purpose of the platform and how your profile information contributes to the assessment.</li>
              <li>Once these acknowledgements are complete, you can move into the guided insurance assessment.</li>
            </ul>
          </section>

          <section className="glass-panel rounded-[2rem] p-6 sm:p-8">
            <div className="rounded-[1.75rem] bg-slate-950 p-6 text-white">
              <p className="text-xs uppercase tracking-[0.32em] text-cyan-200">Data-use summary</p>
              <p className="mt-4 text-sm leading-7 text-slate-200">
                Your assessment information helps generate premium estimates, explain the most important risk drivers,
                and support future cost forecasting. Privacy-sensitive data is handled carefully throughout the process.
              </p>
            </div>

            <div className="mt-6 space-y-4">
              <label className="flex gap-4 rounded-[1.5rem] border border-slate-200 bg-white p-5">
                <input
                  type="checkbox"
                  checked={state.consent_accepted}
                  onChange={(event) => setState((current) => ({ ...current, consent_accepted: event.target.checked }))}
                  className="mt-1 h-5 w-5 rounded border-slate-300"
                />
                <span className="text-sm leading-7 text-slate-700">
                  I consent to the use of my health-related profile data for pricing analysis and risk forecasting.
                </span>
              </label>
              <label className="flex gap-4 rounded-[1.5rem] border border-slate-200 bg-white p-5">
                <input
                  type="checkbox"
                  checked={state.platform_purpose_seen}
                  onChange={(event) => setState((current) => ({ ...current, platform_purpose_seen: event.target.checked }))}
                  className="mt-1 h-5 w-5 rounded border-slate-300"
                />
                <span className="text-sm leading-7 text-slate-700">
                  I understand this platform is designed to support premium prediction, risk explanation, and coverage planning.
                </span>
              </label>
              <label className="flex gap-4 rounded-[1.5rem] border border-slate-200 bg-white p-5">
                <input
                  type="checkbox"
                  checked={state.data_use_summary_seen}
                  onChange={(event) => setState((current) => ({ ...current, data_use_summary_seen: event.target.checked }))}
                  className="mt-1 h-5 w-5 rounded border-slate-300"
                />
                <span className="text-sm leading-7 text-slate-700">
                  I have reviewed the summary explaining how my information is used to produce insights and reporting outputs.
                </span>
              </label>
            </div>

            {error && (
              <div className="mt-5 rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
                {error}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !state.consent_accepted || !state.platform_purpose_seen || !state.data_use_summary_seen}
              className="mt-6 w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isSubmitting ? "Saving onboarding..." : "Continue to assessment"}
            </button>
          </section>
        </div>
      </AppShell>
    </RequireAuth>
  );
}
