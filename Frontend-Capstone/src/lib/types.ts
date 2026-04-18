export type UserSummary = {
  id: number;
  email: string;
  role: "user" | "admin";
  tenant_name: string;
  onboarded: boolean;
  is_active: boolean;
  created_at: string;
};

export type LoginChallengeResponse = {
  challenge_id: string;
  mfa_required: boolean;
  challenge_expires_at: string;
  otp_code_preview?: string | null;
  message: string;
};

export type AuthTokensResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_seconds: number;
  user: UserSummary;
};

export type SignupResponse = {
  message: string;
  user: UserSummary;
};

export type OnboardingResponse = {
  message: string;
  onboarded: boolean;
  consent_version: string;
};

export type PatientProfileInput = {
  age: number;
  bmi: number;
  smoker_status: boolean;
  dependents: number;
  region: string;
  sex: string;
  recent_hospitalizations: number;
  base_risk_score: number;
  subscription_tier: string;
  tenant_company?: string | null;
  consent_to_model_improvement: boolean;
};

export type PatientProfileResponse = PatientProfileInput & {
  id: number;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProfileUpsertResponse = {
  message: string;
  profile: PatientProfileResponse;
};

export type ExplainabilityFactor = {
  feature_name: string;
  value: number;
  direction: string;
  plain_language: string;
};

export type PredictionResponse = {
  premium_estimate_monthly: number;
  risk_probability: number;
  risk_level: string;
  confidence_indicator: string;
  explanation_method: string;
  top_driver: string;
  top_factors: ExplainabilityFactor[];
  explanation_markdown: string;
  status: string;
  profile_version?: number | null;
};

export type ForecastResponse = {
  current_premium_estimate: number;
  months: string[];
  historical_premiums: number[];
  forecast_premiums: number[];
  trend_summary: string;
  status: string;
};

export type ComingSoonResponse = {
  status: "coming_soon";
  feature: string;
  message: string;
};

export type AdminMetricsResponse = {
  total_users: number;
  active_users: number;
  avg_response_time_ms: number;
  error_rate: number;
};

export type WorkflowSplitItem = {
  feature_type: string;
  count: number;
  percentage: number;
};

export type UsageFunnel = {
  prediction_views: number;
  forecast_views: number;
  recommendation_views: number;
};

export type FeatureUsageMetric = {
  feature_type: string;
  request_volume: number;
};

export type TrendPoint = {
  bucket: string;
  total_events: number;
  prediction_events: number;
  forecast_events: number;
  recommendation_events: number;
};

export type AdminDashboardResponse = {
  accounts: {
    accounts_created: number;
    active_users: number;
  };
  feature_usage: FeatureUsageMetric[];
  model_usage: {
    prediction_runs: number;
    forecast_runs: number;
    average_risk_probability: number;
    model_name: string;
    model_version: string;
  };
  workflow_split: WorkflowSplitItem[];
  usage_funnel: UsageFunnel;
  saas_metrics: {
    api_calls: number;
    per_feature_request_volume: Record<string, number>;
    adoption_by_tenant: Record<string, number>;
  };
  operations: {
    avg_latency_ms: number;
    p95_latency_ms: number;
    error_rate: number;
    availability: number;
    slo_summary: Record<string, string | number | boolean>;
  };
  trends: TrendPoint[];
};

export type TrainingExportResponse = {
  job_id: string;
  row_count: number;
  output_path: string;
  created_at: string;
};

export type AppSession = {
  accessToken: string;
  refreshToken: string;
  expiresInSeconds: number;
  createdAt: number;
  user: UserSummary;
};
