"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  apiDelete,
  apiDownload,
  apiGet,
  apiPost,
  apiUpload,
  AssessmentTemplate,
  Control,
  Department,
  Entity,
  getCurrentUser,
  Issue,
  isLoggedIn,
  logout,
  Risk,
  RiskAssessment,
  RiskSummaryReport,
} from "@/lib/api";

import { AssessmentLauncherForm } from "./AssessmentLauncherForm";
import { ControlForm } from "./ControlForm";
import { ControlTestHistory } from "./ControlTestHistory";
import { DepartmentForm } from "./DepartmentForm";
import { EntityForm } from "./EntityForm";
import { EvidenceList } from "./EvidenceList";
import { IssueForm } from "./IssueForm";
import { NotificationBell } from "./NotificationBell";
import { HeatmapFilter, RiskHeatmap } from "./RiskHeatmap";
import { RiskForm } from "./RiskForm";
import { Card, DataTable, DetailModal, ReadField } from "./ui";

type Tab = "risks" | "controls" | "issues" | "departments" | "entities" | "assessments";

const TABS: { id: Tab; label: string }[] = [
  { id: "risks", label: "Risks" },
  { id: "controls", label: "Controls" },
  { id: "issues", label: "Issues" },
  { id: "departments", label: "Departments" },
  { id: "entities", label: "Entities" },
  { id: "assessments", label: "Assessments" },
];

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString();
}

function isOverdueVendor(e: Entity): boolean {
  if (e.type !== "Vendor") return false;
  const today = new Date().toISOString().slice(0, 10);
  const oneYearAgo = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  return (!!e.contract_end_date && e.contract_end_date <= today) || (!!e.last_due_diligence_date && e.last_due_diligence_date <= oneYearAgo);
}

export default function WorkspacePage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("risks");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [heatmapFilter, setHeatmapFilter] = useState<HeatmapFilter | null>(null);
  const [loggedIn, setLoggedIn] = useState(() => isLoggedIn());

  const [summary, setSummary] = useState<RiskSummaryReport | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [controls, setControls] = useState<Control[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [templates, setTemplates] = useState<AssessmentTemplate[]>([]);

  const [viewingRisk, setViewingRisk] = useState<Risk | null>(null);
  const [viewingControl, setViewingControl] = useState<Control | null>(null);
  const [viewingIssue, setViewingIssue] = useState<Issue | null>(null);
  const [viewingDepartment, setViewingDepartment] = useState<Department | null>(null);
  const [viewingEntity, setViewingEntity] = useState<Entity | null>(null);
  const [viewingAssessment, setViewingAssessment] = useState<RiskAssessment | null>(null);

  const [riskSearch, setRiskSearch] = useState("");
  const [controlSearch, setControlSearch] = useState("");
  const [issueSearch, setIssueSearch] = useState("");
  const [overdueVendorsOnly, setOverdueVendorsOnly] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);

  function reload() {
    Promise.all([
      apiGet<RiskSummaryReport>("/api/v1/reports/risk-summary"),
      apiGet<Department[]>("/api/v1/departments"),
      apiGet<Entity[]>("/api/v1/entities"),
      apiGet<Risk[]>("/api/v1/risks"),
      apiGet<Control[]>("/api/v1/controls"),
      apiGet<Issue[]>("/api/v1/issues"),
      apiGet<RiskAssessment[]>("/api/v1/risk-assessments"),
      apiGet<AssessmentTemplate[]>("/api/v1/assessment-templates"),
    ])
      .then(([s, d, e, r, c, i, a, t]) => {
        setSummary(s);
        setDepartments(d);
        setEntities(e);
        setRisks(r);
        setControls(c);
        setIssues(i);
        setAssessments(a);
        setTemplates(t);
        setLoadError(null);
      })
      .catch((err) => setLoadError((err as Error).message));
  }

  useEffect(() => {
    reload();
  }, []);

  function requireAuthOrRedirect(): boolean {
    if (isLoggedIn()) return true;
    router.push("/login?next=/workspace");
    return false;
  }

  function handleLogout() {
    logout();
    setLoggedIn(false);
  }

  const entityName = (id: number | null) => entities.find((e) => e.id === id)?.name ?? "—";
  const riskName = (id: number | null) => risks.find((r) => r.id === id)?.name ?? "—";
  const controlName = (id: number | null) => controls.find((c) => c.id === id)?.name ?? "—";

  const filteredRisks = risks
    .filter((r) => (heatmapFilter ? r.inherent_likelihood === heatmapFilter.likelihood && r.inherent_impact === heatmapFilter.impact : true))
    .filter((r) => (riskSearch ? r.name.toLowerCase().includes(riskSearch.toLowerCase()) : true));
  const filteredControls = controls.filter((c) => (controlSearch ? c.name.toLowerCase().includes(controlSearch.toLowerCase()) : true));
  const filteredIssues = issues.filter((i) => (issueSearch ? i.title.toLowerCase().includes(issueSearch.toLowerCase()) : true));
  const filteredEntities = entities.filter((e) => (overdueVendorsOnly ? isOverdueVendor(e) : true));

  async function handleRestartAssessments(scope: "risks" | "entities", id: number) {
    if (!requireAuthOrRedirect()) return;
    try {
      const result = await apiPost<{ restarted_count: number }>(`/api/v1/${scope}/${id}/restart-assessments`, {});
      setImportMessage(`Restarted ${result.restarted_count} assessment(s) back to Not Started.`);
      reload();
    } catch (err) {
      setImportMessage((err as Error).message);
    }
  }

  async function handleImport(resource: "risks" | "controls" | "entities", file: File) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const result = await apiUpload<{ created: number; errors: string[] }>(`/api/v1/${resource}/import`, formData);
      setImportMessage(`Imported ${result.created} row(s).${result.errors.length ? ` ${result.errors.length} error(s): ${result.errors.slice(0, 3).join("; ")}` : ""}`);
      reload();
    } catch (err) {
      setImportMessage((err as Error).message);
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            Interface A
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">GRC Workspace Dashboard</h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            Create risks, controls, issues, departments, and launch assessments.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <NotificationBell />
          {loggedIn ? (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-zinc-500">Signed in as {getCurrentUser()?.username}</span>
              <button onClick={handleLogout} className="text-zinc-500 hover:underline">
                Sign out
              </button>
            </div>
          ) : (
            <Link href="/login?next=/workspace" className="text-sm text-zinc-500 hover:underline">
              Sign in
            </Link>
          )}
          <Link href="/" className="text-sm text-zinc-500 hover:underline">
            ← Home
          </Link>
        </div>
      </div>

      {loadError && (
        <p className="mb-6 rounded-md border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {loadError}. Is the FastAPI backend running on port 8050?
        </p>
      )}
      {importMessage && (
        <p className="mb-6 flex items-center justify-between rounded-md border border-zinc-300 bg-zinc-50 px-4 py-2 text-sm text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
          {importMessage}
          <button onClick={() => setImportMessage(null)} className="ml-4 text-zinc-400 hover:text-zinc-700">
            ✕
          </button>
        </p>
      )}

      {summary && (
        <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Total Risks" value={String(summary.total_risks)} />
          <StatCard
            label="Avg Inherent / Residual"
            value={`${summary.avg_inherent_score ?? "—"} / ${summary.avg_residual_score ?? "—"}`}
          />
          <StatCard label="Open Issues" value={String(summary.open_issue_count)} />
          <StatCard
            label="Control Compliance"
            value={summary.control_compliance_pct != null ? `${summary.control_compliance_pct}%` : "—"}
          />
        </div>
      )}
      <div className="mb-8 flex items-center gap-3">
        <button
          onClick={() => apiDownload("/api/v1/reports/risk-summary/pdf")}
          className="text-sm text-zinc-500 hover:underline"
        >
          Export board PDF
        </button>
        <button
          onClick={() =>
            apiPost("/api/v1/reports/snapshot", {}).then(() =>
              setImportMessage("Snapshot recorded for trend history.")
            )
          }
          className="text-sm text-zinc-500 hover:underline"
        >
          Take trend snapshot
        </button>
      </div>

      <div className="mb-6 flex gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium transition ${
              tab === t.id
                ? "border-b-2 border-zinc-900 text-zinc-900 dark:border-white dark:text-white"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "risks" && (
        <div className="grid gap-6">
          <Card title="Create Risk">
            <RiskForm entities={entities} onSaved={(r) => setRisks((prev) => [...prev, r])} />
          </Card>
          <Card title="Heatmap Matrix">
            <RiskHeatmap risks={risks} selected={heatmapFilter} onSelectCell={setHeatmapFilter} />
          </Card>
          <Card
            title={
              heatmapFilter
                ? `Risks (${filteredRisks.length} of ${risks.length} — Likelihood ${heatmapFilter.likelihood} × Impact ${heatmapFilter.impact})`
                : `Risks (${filteredRisks.length} of ${risks.length})`
            }
          >
            <div className="mb-3 flex items-center gap-3">
              <input
                className="w-64 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                placeholder="Search risks…"
                value={riskSearch}
                onChange={(e) => setRiskSearch(e.target.value)}
              />
              <button onClick={() => apiDownload("/api/v1/risks/export")} className="text-sm text-zinc-500 hover:underline">
                Export CSV
              </button>
              <label className="cursor-pointer text-sm text-zinc-500 hover:underline">
                Import CSV
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleImport("risks", e.target.files[0])}
                />
              </label>
            </div>
            <DataTable
              rows={filteredRisks}
              onRowClick={(r) => setViewingRisk(r)}
              onDelete={(id) => {
                if (!requireAuthOrRedirect()) return;
                apiDelete(`/api/v1/risks/${id}`).then(() => setRisks((prev) => prev.filter((r) => r.id !== id)));
              }}
              columns={[
                { header: "Name", render: (r) => r.name, sortValue: (r) => r.name },
                { header: "Entity", render: (r) => entityName(r.entity_id), sortValue: (r) => entityName(r.entity_id) },
                { header: "State", render: (r) => r.state, sortValue: (r) => r.state },
                { header: "Assigned To", render: (r) => r.assigned_to ?? "—", sortValue: (r) => r.assigned_to },
                {
                  header: "Inherent",
                  render: (r) =>
                    r.inherent_likelihood && r.inherent_impact
                      ? r.inherent_likelihood * r.inherent_impact
                      : "—",
                  sortValue: (r) =>
                    r.inherent_likelihood && r.inherent_impact ? r.inherent_likelihood * r.inherent_impact : null,
                },
                {
                  header: "Residual",
                  render: (r) =>
                    r.residual_likelihood && r.residual_impact
                      ? r.residual_likelihood * r.residual_impact
                      : "—",
                  sortValue: (r) =>
                    r.residual_likelihood && r.residual_impact ? r.residual_likelihood * r.residual_impact : null,
                },
                {
                  header: "Appetite",
                  render: (r) =>
                    r.breaches_appetite ? (
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700 dark:bg-red-950 dark:text-red-300">
                        Breach
                      </span>
                    ) : (
                      "—"
                    ),
                  sortValue: (r) => (r.breaches_appetite ? 1 : 0),
                },
                { header: "Created", render: (r) => formatDateTime(r.created_at), sortValue: (r) => r.created_at },
                { header: "Updated", render: (r) => formatDateTime(r.updated_at), sortValue: (r) => r.updated_at },
              ]}
            />
          </Card>
        </div>
      )}

      {tab === "controls" && (
        <div className="grid gap-6">
          <Card title="Create Control">
            <ControlForm
              entities={entities}
              risks={risks}
              onSaved={(c) => setControls((prev) => [...prev, c])}
            />
          </Card>
          <Card title={`Controls (${filteredControls.length} of ${controls.length})`}>
            <div className="mb-3 flex items-center gap-3">
              <input
                className="w-64 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                placeholder="Search controls…"
                value={controlSearch}
                onChange={(e) => setControlSearch(e.target.value)}
              />
              <button onClick={() => apiDownload("/api/v1/controls/export")} className="text-sm text-zinc-500 hover:underline">
                Export CSV
              </button>
              <label className="cursor-pointer text-sm text-zinc-500 hover:underline">
                Import CSV
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleImport("controls", e.target.files[0])}
                />
              </label>
            </div>
            <DataTable
              rows={filteredControls}
              onRowClick={(c) => setViewingControl(c)}
              onDelete={(id) => {
                if (!requireAuthOrRedirect()) return;
                apiDelete(`/api/v1/controls/${id}`).then(() => setControls((prev) => prev.filter((c) => c.id !== id)));
              }}
              columns={[
                { header: "Name", render: (c) => c.name, sortValue: (c) => c.name },
                { header: "Status", render: (c) => c.status, sortValue: (c) => c.status },
                { header: "Entity", render: (c) => entityName(c.entity_id), sortValue: (c) => entityName(c.entity_id) },
                { header: "Mitigates", render: (c) => riskName(c.risk_id), sortValue: (c) => riskName(c.risk_id) },
                { header: "Connector", render: (c) => c.test_connector_type ?? "—", sortValue: (c) => c.test_connector_type },
                { header: "Created", render: (c) => formatDateTime(c.created_at), sortValue: (c) => c.created_at },
                { header: "Updated", render: (c) => formatDateTime(c.updated_at), sortValue: (c) => c.updated_at },
              ]}
            />
          </Card>
        </div>
      )}

      {tab === "issues" && (
        <div className="grid gap-6">
          <Card title="Log Issue">
            <IssueForm
              risks={risks}
              controls={controls}
              onSaved={(i) => setIssues((prev) => [...prev, i])}
            />
          </Card>
          <Card title={`Issues (${filteredIssues.length} of ${issues.length})`}>
            <div className="mb-3">
              <input
                className="w-64 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                placeholder="Search issues…"
                value={issueSearch}
                onChange={(e) => setIssueSearch(e.target.value)}
              />
            </div>
            <DataTable
              rows={filteredIssues}
              onRowClick={(i) => setViewingIssue(i)}
              onDelete={(id) => {
                if (!requireAuthOrRedirect()) return;
                apiDelete(`/api/v1/issues/${id}`).then(() => setIssues((prev) => prev.filter((i) => i.id !== id)));
              }}
              columns={[
                { header: "Title", render: (i) => i.title, sortValue: (i) => i.title },
                { header: "Priority", render: (i) => i.priority, sortValue: (i) => i.priority },
                { header: "State", render: (i) => i.state, sortValue: (i) => i.state },
                { header: "Source", render: (i) => i.source, sortValue: (i) => i.source },
                { header: "Related Risk", render: (i) => riskName(i.risk_id), sortValue: (i) => riskName(i.risk_id) },
                { header: "Related Control", render: (i) => controlName(i.control_id), sortValue: (i) => controlName(i.control_id) },
                { header: "Created", render: (i) => formatDateTime(i.created_at), sortValue: (i) => i.created_at },
                { header: "Updated", render: (i) => formatDateTime(i.updated_at), sortValue: (i) => i.updated_at },
              ]}
            />
          </Card>
        </div>
      )}

      {tab === "departments" && (
        <div className="grid gap-6">
          <Card title="Create Department">
            <DepartmentForm onSaved={(d) => setDepartments((prev) => [...prev, d])} />
          </Card>
          <Card title={`Departments (${departments.length})`}>
            <DataTable
              rows={departments}
              onRowClick={(d) => setViewingDepartment(d)}
              onDelete={(id) => {
                if (!requireAuthOrRedirect()) return;
                apiDelete(`/api/v1/departments/${id}`).then(() => setDepartments((prev) => prev.filter((d) => d.id !== id)));
              }}
              columns={[
                { header: "Name", render: (d) => d.name, sortValue: (d) => d.name },
                { header: "Manager", render: (d) => d.manager_id ?? "—", sortValue: (d) => d.manager_id },
                { header: "Cost Center", render: (d) => d.cost_center ?? "—", sortValue: (d) => d.cost_center },
                { header: "Created", render: (d) => formatDateTime(d.created_at), sortValue: (d) => d.created_at },
                { header: "Updated", render: (d) => formatDateTime(d.updated_at), sortValue: (d) => d.updated_at },
              ]}
            />
          </Card>
        </div>
      )}

      {tab === "entities" && (
        <div className="grid gap-6">
          <Card title="Create Entity">
            <EntityForm departments={departments} onSaved={(e) => setEntities((prev) => [...prev, e])} />
          </Card>
          <Card title={`Entities (${filteredEntities.length} of ${entities.length})`}>
            <div className="mb-3 flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={overdueVendorsOnly}
                  onChange={(e) => setOverdueVendorsOnly(e.target.checked)}
                />
                Overdue vendors only
              </label>
              <button onClick={() => apiDownload("/api/v1/entities/export")} className="text-sm text-zinc-500 hover:underline">
                Export CSV
              </button>
              <label className="cursor-pointer text-sm text-zinc-500 hover:underline">
                Import CSV
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleImport("entities", e.target.files[0])}
                />
              </label>
            </div>
            <DataTable
              rows={filteredEntities}
              onRowClick={(e) => setViewingEntity(e)}
              onDelete={(id) => {
                if (!requireAuthOrRedirect()) return;
                apiDelete(`/api/v1/entities/${id}`).then(() => setEntities((prev) => prev.filter((e) => e.id !== id)));
              }}
              columns={[
                { header: "Name", render: (e) => e.name, sortValue: (e) => e.name },
                { header: "Type", render: (e) => e.type, sortValue: (e) => e.type },
                {
                  header: "Department",
                  render: (e) => departments.find((d) => d.id === e.department_id)?.name ?? "—",
                  sortValue: (e) => departments.find((d) => d.id === e.department_id)?.name ?? null,
                },
                { header: "Status", render: (e) => e.status, sortValue: (e) => e.status },
                {
                  header: "Vendor Review",
                  render: (e) =>
                    isOverdueVendor(e) ? (
                      <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700 dark:bg-orange-950 dark:text-orange-300">
                        Overdue
                      </span>
                    ) : e.type === "Vendor" ? (
                      "Current"
                    ) : (
                      "—"
                    ),
                  sortValue: (e) => (e.type === "Vendor" ? (isOverdueVendor(e) ? 1 : 0) : null),
                },
                { header: "Created", render: (e) => formatDateTime(e.created_at), sortValue: (e) => e.created_at },
                { header: "Updated", render: (e) => formatDateTime(e.updated_at), sortValue: (e) => e.updated_at },
              ]}
            />
          </Card>
        </div>
      )}

      {tab === "assessments" && (
        <div className="grid gap-6">
          <Card title="Launch Risk Assessment">
            <AssessmentLauncherForm
              risks={risks}
              templates={templates}
              onSaved={(a) => setAssessments((prev) => [...prev, a])}
            />
          </Card>
          <Card title={`Assessments (${assessments.length})`}>
            <div className="mb-3">
              <button
                onClick={() => {
                  if (!requireAuthOrRedirect()) return;
                  apiPost<{ generated: number }>("/api/v1/assessments/generate-recurring", {}).then((r) => {
                    setImportMessage(`Generated ${r.generated} recurring assessment(s).`);
                    reload();
                  });
                }}
                className="text-sm text-zinc-500 hover:underline"
              >
                Generate due recurring assessments
              </button>
            </div>
            <DataTable
              rows={assessments}
              onRowClick={(a) => setViewingAssessment(a)}
              columns={[
                { header: "Risk", render: (a) => riskName(a.risk_id), sortValue: (a) => riskName(a.risk_id) },
                { header: "Assessor", render: (a) => a.assessor_id ?? "—", sortValue: (a) => a.assessor_id },
                { header: "State", render: (a) => a.state, sortValue: (a) => a.state },
                { header: "Score", render: (a) => a.score ?? "—", sortValue: (a) => a.score },
                { header: "Created", render: (a) => formatDateTime(a.created_at), sortValue: (a) => a.created_at },
                { header: "Updated", render: (a) => formatDateTime(a.updated_at), sortValue: (a) => a.updated_at },
              ]}
            />
          </Card>
        </div>
      )}

      {viewingRisk && (
        <DetailModal
          title={`Risk: ${viewingRisk.name}`}
          record={viewingRisk}
          onClose={() => setViewingRisk(null)}
          onSaved={(updated) =>
            setRisks((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
          }
          renderView={(r) => (
            <>
              <ReadField label="Name" value={r.name} />
              <ReadField label="Entity" value={entityName(r.entity_id)} />
              <ReadField label="State" value={r.state} />
              <ReadField label="Assigned To" value={r.assigned_to} />
              <ReadField label="Inherent Likelihood" value={r.inherent_likelihood} />
              <ReadField label="Inherent Impact" value={r.inherent_impact} />
              <ReadField label="Residual Likelihood" value={r.residual_likelihood} />
              <ReadField label="Residual Impact" value={r.residual_impact} />
              <ReadField label="Breaches Appetite" value={r.breaches_appetite ? "Yes" : "No"} />
              <div className="sm:col-span-2">
                <ReadField label="Description" value={r.description} />
              </div>
              <div className="sm:col-span-2">
                <button
                  onClick={() => handleRestartAssessments("risks", r.id)}
                  className="text-sm text-zinc-500 hover:underline"
                >
                  Restart assessments for this risk
                </button>
              </div>
              <EvidenceList recordType="risk" recordId={r.id} />
            </>
          )}
          renderEdit={(r, onSaved, onCancel) => (
            <RiskForm entities={entities} record={r} onSaved={onSaved} onCancel={onCancel} />
          )}
        />
      )}

      {viewingControl && (
        <DetailModal
          title={`Control: ${viewingControl.name}`}
          record={viewingControl}
          onClose={() => setViewingControl(null)}
          onSaved={(updated) =>
            setControls((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
          }
          renderView={(c) => (
            <>
              <ReadField label="Name" value={c.name} />
              <ReadField label="Status" value={c.status} />
              <ReadField label="Entity" value={entityName(c.entity_id)} />
              <ReadField label="Mitigates Risk" value={riskName(c.risk_id)} />
              <ReadField label="Test Connector" value={c.test_connector_type ?? "None"} />
              <div className="sm:col-span-2">
                <ReadField label="Description" value={c.description} />
              </div>
              <ControlTestHistory controlId={c.id} />
              <EvidenceList recordType="control" recordId={c.id} />
            </>
          )}
          renderEdit={(c, onSaved, onCancel) => (
            <ControlForm
              entities={entities}
              risks={risks}
              record={c}
              onSaved={onSaved}
              onCancel={onCancel}
            />
          )}
        />
      )}

      {viewingIssue && (
        <DetailModal
          title={`Issue: ${viewingIssue.title}`}
          record={viewingIssue}
          onClose={() => setViewingIssue(null)}
          onSaved={(updated) =>
            setIssues((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))
          }
          renderView={(i) => (
            <>
              <ReadField label="Title" value={i.title} />
              <ReadField label="Priority" value={i.priority} />
              <ReadField label="State" value={i.state} />
              <ReadField label="Source" value={i.source} />
              <ReadField label="Assigned To" value={i.assigned_to} />
              <ReadField label="Related Risk" value={riskName(i.risk_id)} />
              <ReadField label="Related Control" value={controlName(i.control_id)} />
              <div className="sm:col-span-2">
                <ReadField label="Description" value={i.description} />
              </div>
              <ReadField label="Root Cause" value={i.root_cause} />
              <ReadField label="Corrective Action" value={i.corrective_action} />
              <ReadField label="Effectiveness Check Date" value={i.effectiveness_check_date} />
              <ReadField label="Recurrence Count" value={i.recurrence_count} />
              <EvidenceList recordType="issue" recordId={i.id} />
            </>
          )}
          renderEdit={(i, onSaved, onCancel) => (
            <IssueForm
              risks={risks}
              controls={controls}
              record={i}
              onSaved={onSaved}
              onCancel={onCancel}
            />
          )}
        />
      )}

      {viewingDepartment && (
        <DetailModal
          title={`Department: ${viewingDepartment.name}`}
          record={viewingDepartment}
          onClose={() => setViewingDepartment(null)}
          onSaved={(updated) =>
            setDepartments((prev) => prev.map((d) => (d.id === updated.id ? updated : d)))
          }
          renderView={(d) => (
            <>
              <ReadField label="Name" value={d.name} />
              <ReadField label="Manager ID" value={d.manager_id} />
              <ReadField label="Cost Center" value={d.cost_center} />
            </>
          )}
          renderEdit={(d, onSaved, onCancel) => (
            <DepartmentForm record={d} onSaved={onSaved} onCancel={onCancel} />
          )}
        />
      )}

      {viewingEntity && (
        <DetailModal
          title={`Entity: ${viewingEntity.name}`}
          record={viewingEntity}
          onClose={() => setViewingEntity(null)}
          onSaved={(updated) =>
            setEntities((prev) => prev.map((e) => (e.id === updated.id ? updated : e)))
          }
          renderView={(e) => (
            <>
              <ReadField label="Name" value={e.name} />
              <ReadField label="Type" value={e.type} />
              <ReadField label="Department" value={departments.find((d) => d.id === e.department_id)?.name} />
              <ReadField label="Owner" value={e.owner_id} />
              <ReadField label="Status" value={e.status} />
              <ReadField label="Criticality Tier" value={e.criticality_tier} />
              <ReadField label="Contract End Date" value={e.contract_end_date} />
              <ReadField label="Last Due Diligence" value={e.last_due_diligence_date} />
              <div className="sm:col-span-2">
                <button
                  onClick={() => handleRestartAssessments("entities", e.id)}
                  className="text-sm text-zinc-500 hover:underline"
                >
                  Restart assessments for all risks under this entity
                </button>
              </div>
            </>
          )}
          renderEdit={(e, onSaved, onCancel) => (
            <EntityForm departments={departments} record={e} onSaved={onSaved} onCancel={onCancel} />
          )}
        />
      )}

      {viewingAssessment && (
        <DetailModal
          title={`Assessment: ${riskName(viewingAssessment.risk_id)}`}
          record={viewingAssessment}
          onClose={() => setViewingAssessment(null)}
          onSaved={(updated) =>
            setAssessments((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
          }
          renderView={(a) => (
            <>
              <ReadField label="Risk" value={riskName(a.risk_id)} />
              <ReadField label="Assessor" value={a.assessor_id} />
              <ReadField label="State" value={a.state} />
              <ReadField label="Score" value={a.score} />
              <div className="sm:col-span-2">
                <ReadField label="Comments" value={a.comments} />
              </div>
              <EvidenceList recordType="assessment" recordId={a.id} />
            </>
          )}
          renderEdit={(a, onSaved, onCancel) => (
            <AssessmentLauncherForm
              risks={risks}
              templates={templates}
              record={a}
              onSaved={onSaved}
              onCancel={onCancel}
            />
          )}
        />
      )}
    </div>
  );
}
