"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiRequest, persistTokens } from "@/lib/api";
import { getAuthenticatedHome } from "@/lib/constants";
import { useSession } from "@/components/providers/SessionProvider";
import type { AuthTokensResponse, LoginChallengeResponse } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const { session, setSession } = useSession();
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [challenge, setChallenge] = useState<LoginChallengeResponse | null>(null);
  const [otp, setOtp] = useState("");
  const [nextPath] = useState(() =>
    typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("next") || "" : "",
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (session) {
      router.replace(nextPath || getAuthenticatedHome(session));
    }
  }, [nextPath, router, session]);

  const handleCredentialsSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await apiRequest<LoginChallengeResponse>("/auth/login", {
        method: "POST",
        body: credentials,
        retryOnUnauthorized: false,
      });
      setChallenge(response);
      if (response.otp_code_preview) {
        setOtp(response.otp_code_preview);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to start login.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifySubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!challenge) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await apiRequest<AuthTokensResponse>("/auth/mfa/verify", {
        method: "POST",
        body: { challenge_id: challenge.challenge_id, otp },
        retryOnUnauthorized: false,
      });
      const nextSession = persistTokens(response);
      setSession(nextSession);
      router.replace(nextPath || getAuthenticatedHome(nextSession));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to verify MFA.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.22),_transparent_28%),linear-gradient(180deg,_#f6f0e2_0%,_#f8fafc_100%)] px-4 py-10 sm:px-6">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="glass-panel rounded-[2.5rem] p-8 sm:p-10">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-700">Secure platform access</p>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight text-slate-950">Authenticate into Medisight AI.</h1>
          <p className="mt-5 text-base leading-8 text-slate-600">
            Sign in to continue your premium assessment journey. Access is protected with a second verification step to
            keep personal insurance data secure.
          </p>
          <div className="mt-8 space-y-4 rounded-[2rem] bg-slate-950 p-6 text-white">
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-200">Protected sign-in</p>
            <p className="text-sm text-slate-300">
              Use your assigned credentials to begin. You will then confirm your identity with a one-time verification
              code before entering the platform.
            </p>
            <p className="text-sm text-slate-300">
              A second verification step helps protect personal insurance information and maintain trusted access.
            </p>
          </div>
        </section>

        <section className="glass-panel rounded-[2.5rem] p-8 sm:p-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">Account login</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                {challenge ? "Verify your access code" : "Enter your credentials"}
              </h2>
            </div>
            <Link href="/" className="text-sm text-slate-500 underline-offset-4 hover:text-slate-950 hover:underline">
              Home
            </Link>
          </div>

          {error && (
            <div className="mt-6 rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
              {error}
            </div>
          )}

          {!challenge ? (
            <form className="mt-8 space-y-5" onSubmit={handleCredentialsSubmit}>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
                <input
                  type="email"
                  required
                  value={credentials.email}
                  onChange={(event) => setCredentials((current) => ({ ...current, email: event.target.value }))}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none ring-0 focus:border-cyan-400"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
                <input
                  type="password"
                  required
                  value={credentials.password}
                  onChange={(event) => setCredentials((current) => ({ ...current, password: event.target.value }))}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none ring-0 focus:border-cyan-400"
                />
              </label>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isSubmitting ? "Starting secure session..." : "Continue to MFA"}
              </button>
            </form>
          ) : (
            <form className="mt-8 space-y-5" onSubmit={handleVerifySubmit}>
              <div className="rounded-[1.5rem] border border-cyan-200 bg-cyan-50 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-700">Challenge ready</p>
                <p className="mt-3 text-sm leading-6 text-slate-700">{challenge.message}</p>
                {challenge.otp_code_preview && (
                  <p className="mt-4 text-sm text-slate-700">
                    Verification code: <span className="font-semibold text-slate-950">{challenge.otp_code_preview}</span>
                  </p>
                )}
              </div>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">One-time code</span>
                <input
                  type="text"
                  required
                  minLength={6}
                  maxLength={6}
                  value={otp}
                  onChange={(event) => setOtp(event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-center text-lg tracking-[0.5em] text-slate-900 outline-none ring-0 focus:border-cyan-400"
                />
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setChallenge(null);
                    setOtp("");
                  }}
                  className="flex-1 rounded-full border border-slate-200 bg-white px-5 py-4 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isSubmitting ? "Verifying..." : "Finish sign in"}
                </button>
              </div>
            </form>
          )}

          <div className="mt-8 flex items-center justify-between text-sm text-slate-500">
            <p>
              Need an account?{" "}
              <Link href="/signup" className="font-medium text-slate-950 underline-offset-4 hover:underline">
                Create one
              </Link>
            </p>
            <Link href="/reset-password" className="font-medium text-slate-950 underline-offset-4 hover:underline">
              Reset password
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
