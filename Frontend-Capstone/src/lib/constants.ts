import type { AppSession, PatientProfileInput } from "@/lib/types";

export const REGIONS = [
  "Ontario",
  "Quebec",
  "British Columbia",
  "Alberta",
  "Manitoba",
  "Saskatchewan",
  "Nova Scotia",
  "New Brunswick",
] as const;

export const SEXES = ["Male", "Female", "Non-binary"] as const;

export const SUBSCRIPTION_TIERS = ["Standard", "Premium", "Enterprise"] as const;

export const DEFAULT_PROFILE: PatientProfileInput = {
  age: 38,
  bmi: 26.4,
  smoker_status: false,
  dependents: 1,
  region: REGIONS[0],
  sex: SEXES[0],
  recent_hospitalizations: 0,
  base_risk_score: 20,
  subscription_tier: SUBSCRIPTION_TIERS[0],
  tenant_company: "",
  consent_to_model_improvement: true,
};

export function getAuthenticatedHome(session: AppSession | null): string {
  if (!session) {
    return "/login";
  }
  if (session.user.role === "admin") {
    return "/admin";
  }
  return session.user.onboarded ? "/assessment" : "/onboarding";
}
