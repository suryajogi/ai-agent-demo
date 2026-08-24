export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${init?.method ?? "GET"} ${path} failed (${res.status}): ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const apiGet = <T>(path: string) => request<T>(path);
export const apiPost = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });
export const apiPut = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PUT", body: JSON.stringify(body) });
export const apiDelete = (path: string) => request<void>(path, { method: "DELETE" });

// --- Domain types (mirror backend/schemas.py) --------------------------------

export interface Department {
  id: number;
  name: string;
  manager_id: string | null;
  cost_center: string | null;
}

export interface Entity {
  id: number;
  name: string;
  type: string;
  department_id: number | null;
  owner_id: string | null;
  status: string;
}

export interface Risk {
  id: number;
  name: string;
  description: string | null;
  statement_id: number | null;
  entity_id: number | null;
  assigned_to: string | null;
  state: string;
  inherent_likelihood: number | null;
  inherent_impact: number | null;
  residual_likelihood: number | null;
  residual_impact: number | null;
}

export interface RiskAssessment {
  id: number;
  risk_id: number | null;
  assessor_id: string | null;
  template_id: number | null;
  state: string;
  score: number | null;
  comments: string | null;
}

export interface Control {
  id: number;
  name: string;
  description: string | null;
  status: string;
  entity_id: number | null;
  risk_id: number | null;
}

export interface Issue {
  id: number;
  title: string;
  description: string | null;
  source: string;
  priority: string;
  state: string;
  assigned_to: string | null;
  risk_id: number | null;
  control_id: number | null;
}

export interface AssessmentTemplate {
  id: number;
  name: string;
  description: string | null;
  metric_type: string;
}

export interface AssessmentQuestion {
  id: number;
  template_id: number | null;
  question_text: string;
  weight: number;
}

export interface AssessmentResponse {
  id: number;
  assessment_id: number | null;
  question_id: number | null;
  selected_value: number;
  justification: string | null;
}

export interface RiskAssessmentWithResponses extends RiskAssessment {
  responses: AssessmentResponse[];
}

export interface RiskSummaryReport {
  total_risks: number;
  risks_by_state: Record<string, number>;
  avg_inherent_score: number | null;
  avg_residual_score: number | null;
  risk_reduction_pct: number | null;
  open_issue_count: number;
  issues_by_priority: Record<string, number>;
  total_controls: number;
  controls_by_status: Record<string, number>;
  control_compliance_pct: number | null;
}

export interface DashboardStats {
  totalRisks: number;
  openIssues: number;
  activeControls: number;
  pendingAssessments: number;
}

export const RISK_STATES = ["Draft", "Assess", "Respond", "Review", "Monitor"];
export const CONTROL_STATUSES = ["Draft", "Attest", "Review", "Monitor"];
export const ISSUE_SOURCES = ["Risk Assessment", "Control Failure", "Manual"];
export const ISSUE_PRIORITIES = ["Low", "Medium", "High", "Critical"];
export const ISSUE_STATES = ["New", "Analyze", "Remediate", "Closed"];
export const ASSESSMENT_STATES = ["Not Started", "In Progress", "Completed"];
export const ENTITY_TYPES = ["Application", "Facility", "Vendor"];
