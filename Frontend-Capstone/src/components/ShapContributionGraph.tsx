"use client";

import type { ExplainabilityFactor } from "@/lib/types";

type ShapContributionGraphProps = {
  factors: ExplainabilityFactor[];
  explanationMethod: string;
};

function featureLabel(name: string): string {
  return name.replaceAll("_", " ");
}

export default function ShapContributionGraph({ factors, explanationMethod }: ShapContributionGraphProps) {
  const maxAbs = Math.max(...factors.map((factor) => Math.abs(factor.value)), 0.0001);
  const isShapCompatible = explanationMethod !== "heuristic";
  const graphTitle = isShapCompatible ? "Prediction contribution graph" : "Contribution graph";
  const graphNote =
    explanationMethod === "shap_tree_explainer"
      ? "Computed from SHAP TreeExplainer values."
      : explanationMethod === "xgboost_pred_contrib"
        ? "Computed from XGBoost contribution values compatible with TreeSHAP."
        : "Computed from fallback ranked contribution logic because the ML explainability runtime is unavailable.";

  return (
    <div className="rounded-[1.75rem] bg-white/75 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.32em] text-slate-500">{graphTitle}</p>
          <p className="mt-2 text-sm leading-7 text-slate-600">{graphNote}</p>
        </div>
        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-600">
          {explanationMethod.replaceAll("_", " ")}
        </span>
      </div>

      <div className="mt-6 space-y-4">
        {factors.map((factor) => {
          const magnitude = Math.max((Math.abs(factor.value) / maxAbs) * 100, 8);
          const isNegative = factor.value < 0;

          return (
            <div key={`${factor.feature_name}-${factor.direction}`} className="grid gap-3 md:grid-cols-[180px_minmax(0,1fr)_88px] md:items-center">
              <div>
                <p className="text-sm font-medium capitalize text-slate-950">{featureLabel(factor.feature_name)}</p>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{factor.direction}</p>
              </div>

              <div className="relative h-10 rounded-full bg-slate-100">
                <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-slate-300" />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] uppercase tracking-[0.2em] text-slate-400">
                  Lower risk
                </div>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] uppercase tracking-[0.2em] text-slate-400">
                  Higher risk
                </div>
                <div className={`absolute top-1/2 h-4 -translate-y-1/2 rounded-full ${isNegative ? "bg-emerald-500" : "bg-rose-500"}`}
                  style={
                    isNegative
                      ? { right: "50%", width: `${Math.min(magnitude * 0.48, 48)}%` }
                      : { left: "50%", width: `${Math.min(magnitude * 0.48, 48)}%` }
                  }
                />
              </div>

              <div className="text-right text-sm font-semibold text-slate-950">{factor.value.toFixed(4)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
