"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiRequest } from "@/lib/api";
import { useSession } from "@/components/providers/SessionProvider";
import type { SignupResponse } from "@/lib/types";

export default function SignupPage() {
  const router = useRouter();
  const { session } = useSession();
  const [formData, setFormData] = useState({
    email: "",
    tenant_name: "Pacific Care",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (session) {
      router.replace("/");
    }
  }, [router, session]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      const response = await apiRequest<SignupResponse>("/auth/signup", {
        method: "POST",
        body: {
          email: formData.email,
          tenant_name: formData.tenant_name,
          password: formData.password,
        },
        retryOnUnauthorized: false,
      });
      setSuccess(`${response.message} You can sign in now.`);
      setTimeout(() => router.push("/login"), 1000);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create account.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.18),_transparent_30%),linear-gradient(180deg,_#f6efe0_0%,_#f8fafc_100%)] px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <div className="glass-panel rounded-[2.5rem] p-8 sm:p-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-700">Public user registration</p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">Create a customer account.</h1>
            </div>
            <Link href="/login" className="text-sm text-slate-500 underline-offset-4 hover:text-slate-950 hover:underline">
              Log in
            </Link>
          </div>

          <p className="mt-5 max-w-2xl text-base leading-8 text-slate-600">
            Create your account to begin a guided premium assessment experience with secure access and explainable results.
          </p>

          {error && (
            <div className="mt-6 rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
              {error}
            </div>
          )}
          {success && (
            <div className="mt-6 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
              {success}
            </div>
          )}

          <form className="mt-8 grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit}>
            <label className="block sm:col-span-2">
              <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(event) => setFormData((current) => ({ ...current, email: event.target.value }))}
                className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-cyan-400"
              />
            </label>
            <label className="block sm:col-span-2">
              <span className="mb-2 block text-sm font-medium text-slate-700">Tenant name</span>
              <input
                type="text"
                required
                minLength={2}
                value={formData.tenant_name}
                onChange={(event) => setFormData((current) => ({ ...current, tenant_name: event.target.value }))}
                className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-cyan-400"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
              <input
                type="password"
                required
                minLength={8}
                value={formData.password}
                onChange={(event) => setFormData((current) => ({ ...current, password: event.target.value }))}
                className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-cyan-400"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Confirm password</span>
              <input
                type="password"
                required
                minLength={8}
                value={formData.confirmPassword}
                onChange={(event) => setFormData((current) => ({ ...current, confirmPassword: event.target.value }))}
                className="w-full rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-cyan-400"
              />
            </label>
            <button
              type="submit"
              disabled={isSubmitting}
              className="sm:col-span-2 rounded-full bg-slate-950 px-5 py-4 text-sm font-medium text-white shadow-xl transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isSubmitting ? "Creating account..." : "Create secure account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
