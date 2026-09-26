/**
 * ReLoop AI — Backend API Client
 * Centralized helper for communicating with the FastAPI backend via Next.js rewrites proxy.
 * All backend calls go through /backend-api/* which is silently proxied to http://127.0.0.1:8000/api/*
 */

const BACKEND_PREFIX = "/backend-api";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: { message: res.statusText } }));
    const msg =
      body?.error?.message || body?.detail || body?.message || `Backend error (${res.status})`;
    throw new Error(msg);
  }
  return res.json();
}

// ─── Products ─────────────────────────────────────────────────────────────────

export interface ProductIdentifyResponse {
  identified_model: {
    manufacturer: string;
    model: string;
    model_year: number;
    confidence: string;
    specs: Record<string, any>;
  } | null;
  is_supported: boolean;
  confidence: number;
  visible_label_text: string | null;
  visual_clues: string[];
  needs_confirmation: boolean;
  requires_user_confirmation: boolean;
  alternative_models: Array<{
    manufacturer: string;
    model: string;
    model_year: number;
  }>;
  supported_models: Array<{
    manufacturer: string;
    model: string;
    model_year: number;
  }>;
  message: string | null;
}

export async function identifyProduct(
  images: File[],
  hint?: string,
  manualModel?: string,
  modelId?: string
): Promise<ProductIdentifyResponse> {
  const formData = new FormData();
  images.forEach((img) => formData.append("images", img));
  if (hint) formData.append("hint", hint);
  if (manualModel) formData.append("manual_model", manualModel);
  if (modelId) formData.append("model_id", modelId);

  const res = await fetch(`${BACKEND_PREFIX}/products/identify`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export interface ProductCreatePayload {
  manufacturer: string;
  model: string;
  model_year: number;
  category?: string;
  serial_or_identifier?: string;
  age?: number;
}

export interface ProductRecord {
  id: string;
  manufacturer: string;
  model: string;
  model_year: number;
  category: string;
  serial_or_identifier: string | null;
  age: number;
  specs: Record<string, any>;
  created_at: string;
}

export async function createProduct(data: ProductCreatePayload): Promise<ProductRecord> {
  const res = await fetch(`${BACKEND_PREFIX}/products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function getProduct(productId: string): Promise<ProductRecord> {
  const res = await fetch(`${BACKEND_PREFIX}/products/${productId}`);
  return handleResponse(res);
}

export async function getProductCatalog() {
  const res = await fetch(`${BACKEND_PREFIX}/products/catalog`);
  return handleResponse<Array<{ manufacturer: string; model: string; model_year: number }>>(res);
}

// ─── Vision Analysis ──────────────────────────────────────────────────────────

export interface VisionAnalyzeResponse {
  product_id: string;
  findings: Array<{
    component: string;
    description: string;
    severity: string;
    confidence: number;
    evidence_type: string;
  }>;
  overall_visual_condition: string;
  overall_condition: string;
  evidence_items: Array<Record<string, any>>;
}

export async function analyzeVision(
  productId: string,
  images: File[],
  inspectionNotes?: string
): Promise<VisionAnalyzeResponse> {
  const formData = new FormData();
  formData.append("product_id", productId);
  images.forEach((img) => formData.append("images", img));
  if (inspectionNotes) formData.append("inspection_notes", inspectionNotes);

  const res = await fetch(`${BACKEND_PREFIX}/vision/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

// ─── Diagnostics ──────────────────────────────────────────────────────────────

export interface DiagnosticsValidatePayload {
  product_id: string;
  battery?: {
    design_capacity?: number;
    full_charge_capacity?: number;
    cycle_count?: number;
    health_percent?: number;
  };
  ssd?: {
    health_percent?: number;
    smart_status?: string;
    power_on_hours?: number;
  };
  ram?: {
    test_result: string;
    installed_gb?: number;
  };
  thermals?: {
    max_temp_c?: number;
    throttling_detected: boolean;
  };
  system?: {
    critical_errors: string[];
    post_successful: boolean;
    motherboard_power_stable: boolean;
  };
}

export interface DiagnosticsValidateResponse {
  valid: boolean;
  evidence_items: Array<Record<string, any>>;
  summary: Record<string, string>;
}

export async function validateDiagnostics(
  data: DiagnosticsValidatePayload
): Promise<DiagnosticsValidateResponse> {
  const res = await fetch(`${BACKEND_PREFIX}/diagnostics/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

// ─── Symptoms ─────────────────────────────────────────────────────────────────

export interface SymptomsParsePayload {
  product_id: string;
  symptoms: string[];
  notes?: string;
  intended_use?: string;
  daily_usage_hours?: number;
}

export interface SymptomsParseResponse {
  product_id: string | null;
  parsed_symptoms: Array<{
    component: string;
    symptom: string;
    severity: string;
    user_statement: string;
  }>;
  evidence_items: Array<Record<string, any>>;
  intended_use: string;
}

export async function parseSymptoms(
  data: SymptomsParsePayload
): Promise<SymptomsParseResponse> {
  const res = await fetch(`${BACKEND_PREFIX}/symptoms/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

// ─── Assessment (Condition Profile) ───────────────────────────────────────────

export interface AssessmentBuildResponse {
  product_id: string;
  overall_hardware_health: string;
  components: Record<
    string,
    {
      component: string;
      status: string;
      observations: string[];
      measurements: Record<string, any>;
      confidence: string;
      evidence_ids: string[];
      label: string | null;
      evidence_sources: string[];
      repairable: boolean;
      upgradeable: boolean;
    }
  >;
  all_evidence: Array<Record<string, any>>;
  created_at: string;
}

export async function buildAssessment(
  productId: string
): Promise<AssessmentBuildResponse> {
  const res = await fetch(`${BACKEND_PREFIX}/assessment/build`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId }),
  });
  return handleResponse(res);
}

export async function getAssessment(
  productId: string
): Promise<AssessmentBuildResponse> {
  const res = await fetch(`${BACKEND_PREFIX}/assessment/${productId}`);
  return handleResponse(res);
}

// ─── Recommendations ──────────────────────────────────────────────────────────

export interface RecommendationGeneratePayload {
  product_id: string;
  objective?: string;
}

export interface ScoredPathway {
  pathway: {
    type: string;
    label: string;
    description: string;
    action_steps: string[];
    estimated_cost: { min_val: number; max_val: number; currency: string };
    expected_life_extension_years: { min_val: number; max_val: number };
    environmental_estimate: {
      co2_avoided_kg_min: number;
      co2_avoided_kg_max: number;
      ewaste_diverted_kg: number;
    };
    turnaround_days: { min_val: number; max_val: number };
    assumptions: string[];
    value_retained_percentage: number;
    material_retained_percentage: number;
    target_components: string[];
    eligibility_reason: string;
    is_eligible: boolean;
  };
  score: number;
  rank: number;
  normalized_subscores: Record<string, number>;
}

export interface RecommendationResponse {
  id: string;
  product_id: string;
  selected_pathway: string;
  objective: string;
  score: number;
  alternative_pathways: ScoredPathway[];
  reasoning: string[];
  evidence_ids: string[];
  assumptions: string[];
  explanation: {
    summary: string;
    details: string[];
    assumptions: string[];
    source: string;
  } | null;
  primary_recommendation: ScoredPathway | null;
  second_life: {
    suggested_role: string;
    target_user: string;
    os_recommendation: string;
    workloads: string[];
    basis: string;
  } | null;
  component_recovery: {
    recoverable_parts: string[];
    salvage_value_estimate_usd: number;
    material_recovery_action: string;
  } | null;
  created_at: string;
}

export async function generateRecommendation(
  data: RecommendationGeneratePayload
): Promise<RecommendationResponse> {
  const res = await fetch(`${BACKEND_PREFIX}/recommendations/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

// ─── Reports ──────────────────────────────────────────────────────────────────

export interface ConditionReportResponse {
  id: string;
  assessment_id: string;
  product_id: string;
  product: ProductRecord;
  condition_profile: AssessmentBuildResponse;
  recommendation: RecommendationResponse;
  alternative_pathways: ScoredPathway[];
  impact_estimates: {
    co2_avoided_kg_min: number;
    co2_avoided_kg_max: number;
    ewaste_diverted_kg: number;
    life_extension_years_min: number;
    life_extension_years_max: number;
    estimated_cost_min: number;
    estimated_cost_max: number;
    value_retained_percentage: number;
    material_retained_percentage: number;
  };
  assumptions: string[];
  data_gaps: string[];
  explanation: {
    summary: string;
    details: string[];
    assumptions: string[];
    source: string;
  } | null;
  disclaimer: string;
  timestamp: string;
}

export async function getReport(
  assessmentId: string
): Promise<ConditionReportResponse> {
  const res = await fetch(`${BACKEND_PREFIX}/reports/${assessmentId}`);
  return handleResponse(res);
}

export async function downloadReport(assessmentId: string): Promise<Blob> {
  const res = await fetch(`${BACKEND_PREFIX}/reports/${assessmentId}/download`);
  if (!res.ok) throw new Error("Failed to download report");
  return res.blob();
}

// ─── Health Check ─────────────────────────────────────────────────────────────

export async function checkBackendHealth(): Promise<{
  status: string;
  app: string;
  version: string;
  ai_status: string;
  engine: string;
}> {
  const res = await fetch(`${BACKEND_PREFIX}/health`);
  return handleResponse(res);
}
