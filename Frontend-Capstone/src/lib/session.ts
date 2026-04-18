import type { AppSession, PatientProfileInput, PredictionResponse } from "@/lib/types";

const SESSION_KEY = "medical-ai.session";
const PROFILE_KEY = "medical-ai.profile";
const PREDICTION_KEY = "medical-ai.prediction";

function canUseStorage(): boolean {
  return typeof window !== "undefined";
}

export function loadSession(): AppSession | null {
  if (!canUseStorage()) {
    return null;
  }
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AppSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function saveSession(session: AppSession): void {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.removeItem(SESSION_KEY);
}

export function loadProfile(): PatientProfileInput | null {
  if (!canUseStorage()) {
    return null;
  }
  const raw = window.localStorage.getItem(PROFILE_KEY);
  return raw ? (JSON.parse(raw) as PatientProfileInput) : null;
}

export function saveProfile(profile: PatientProfileInput): void {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function loadPrediction(): PredictionResponse | null {
  if (!canUseStorage()) {
    return null;
  }
  const raw = window.localStorage.getItem(PREDICTION_KEY);
  return raw ? (JSON.parse(raw) as PredictionResponse) : null;
}

export function savePrediction(prediction: PredictionResponse): void {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(PREDICTION_KEY, JSON.stringify(prediction));
}

export function clearAppData(): void {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.removeItem(PROFILE_KEY);
  window.localStorage.removeItem(PREDICTION_KEY);
}
