"use client";

import Link from "next/link";
import { useState } from "react";

import { apiRequest } from "@/lib/api";

type ResetRequestResponse = {
  message: string;
  reset_token_preview?: string | null;
};

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const requestReset = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSubmitting(true);

    try {
      const response = await apiRequest<ResetRequestResponse>("/auth/password-reset/request", {
        method: "POST",
        body: { email },
        retryOnUnauthorized: false,
      });
      setMessage(response.message);
      if (response.reset_token_preview) {
        setResetToken(response.reset_token_preview);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to request reset.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmReset = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSubmitting(true);

    try {
      await apiRequest("/auth/password-reset/confirm", {
        method: "POST",
        body: {
          reset_token: resetToken,
          new_password: newPassword,
        },
        retryOnUnauthorized: false,
      });
      setMessage("Password reset successfully. You can return to login.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to confirm reset.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.16),_transparent_24%),linear-gradient(180deg,_#f6efe0_0%,_#f8fafc_100%)] px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-4xl">
        <div className="glass-panel rounded-[2.5rem] p-8 sm:p-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-700">Password recovery</p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">Request and confirm a reset token.</h1>
            </div>
            <Link href="/login" className="text-sm text-slate-500 underline-offset-4 hover:text-slate-950 hover:underline">
              Back to login
            </Link>
          </div>

          {message && (
            <div className="mt-6 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
              {message}
            </div>
          )}
          {error && (
            <div className="mt-6 rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
              {error}
            </div>
          )}

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <form className="space-y-5 rounded-[2rem] bg-white/75 p-6" onSubmit={requestReset}>
              <h2 className="text-2xl font-semibold text-slate-950">1. Request reset</h2>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:bg-slate-400"
              >
                Request token
              </button>
            </form>

            <form className="space-y-5 rounded-[2rem] bg-white/75 p-6" onSubmit={confirmReset}>
              <h2 className="text-2xl font-semibold text-slate-950">2. Confirm reset</h2>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Reset token</span>
                <input
                  type="text"
                  required
                  value={resetToken}
                  onChange={(event) => setResetToken(event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">New password</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3"
                />
              </label>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:bg-slate-400"
              >
                Save new password
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
