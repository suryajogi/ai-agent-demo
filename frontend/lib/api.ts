export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8050";

const TOKEN_KEY = "grc_token";
const USER_KEY = "grc_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string, user: User) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function getCurrentUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
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

// Deliberate exception to `request()`: multipart bodies must NOT set a JSON
// Content-Type — the browser needs to set its own boundary.
export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`POST ${path} failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<T>;
}

export async function apiDownload(path: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`GET ${path} failed (${res.status})`);
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename=([^;]+)/);
  const filename = match ? match[1].trim() : "download";
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// --- Auth (NR-012) ------------------------------------------------------------

export interface User {
  id: number;
  username: string;
  display_name: string | null;
  email: string | null;
  role_id: number | null;
  active: boolean;
  department_id: number | null;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export async function login(username: string, password: string): Promise<User> {
  const token = await apiPost<Token>("/api/v1/auth/login", { username, password });
  setSession(token.access_token, token.user);
  return token.user;
}

export function logout() {
  clearSession();
}

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
  contract_end_date: string | null;
  criticality_tier: string | null;
  last_due_diligence_date: string | null;
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
  breaches_appetite: boolean;
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
  test_connector_type: string | null;
  test_connector_config: { url?: string; expect_status?: number } | null;
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
  root_cause: string | null;
  corrective_action: string | null;
  effectiveness_check_date: string | null;
  recurrence_count: number;
}

export interface AssessmentTemplate {
  id: number;
  name: string;
  description: string | null;
  metric_type: string;
  recurrence_rule: string | null;
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

// --- New resource types (NR-001..NR-016) --------------------------------------

export interface EvidenceAttachment {
  id: number;
  record_type: string;
  record_id: number;
  file_name: string;
  content_type: string | null;
  uploaded_by: string | null;
  uploaded_at: string;
}

export interface ControlFrameworkMap {
  id: number;
  control_id: number;
  framework_id: number;
  requirement_reference: string | null;
}

export interface RiskFramework {
  id: number;
  name: string;
  description: string | null;
  scope_id: number | null;
}

export interface RiskAppetiteThreshold {
  id: number;
  name: string;
  category: string | null;
  department_id: number | null;
  max_acceptable_score: number;
}

export interface NotificationItem {
  id: number;
  recipient: string;
  subject: string;
  body: string | null;
  related_type: string | null;
  related_id: number | null;
  created_at: string;
  read_at: string | null;
}

export interface RiskScoreSnapshot {
  id: number;
  snapshot_at: string;
  total_risks: number;
  avg_inherent_score: number | null;
  avg_residual_score: number | null;
  open_issue_count: number;
  control_compliance_pct: number | null;
}

export interface ControlTestResult {
  id: number;
  control_id: number;
  tested_at: string;
  result: string;
  detail: string | null;
  connector_type: string | null;
}

export const RISK_STATES = ["Draft", "Assess", "Respond", "Review", "Monitor"];
export const CONTROL_STATUSES = ["Draft", "Attest", "Review", "Monitor"];
export const ISSUE_SOURCES = ["Risk Assessment", "Control Failure", "Manual"];
export const ISSUE_PRIORITIES = ["Low", "Medium", "High", "Critical"];
export const ISSUE_STATES = ["New", "Analyze", "Remediate", "Closed"];
export const ASSESSMENT_STATES = ["Not Started", "In Progress", "Completed"];
export const ENTITY_TYPES = ["Application", "Facility", "Vendor"];
export const CRITICALITY_TIERS = ["Low", "Medium", "High", "Critical"];
export const RECURRENCE_RULES = ["none", "quarterly", "annual"];
export const CONNECTOR_TYPES = ["none", "http_health_check"];
