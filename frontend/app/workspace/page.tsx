"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  apiDelete,
  apiGet,
  AssessmentTemplate,
  Control,
  Department,
  Entity,
  Issue,
  Risk,
  RiskAssessment,
  RiskSummaryReport,
} from "@/lib/api";

import { AssessmentLauncherForm } from "./AssessmentLauncherForm";
import { ControlForm } from "./ControlForm";
import { DepartmentForm } from "./DepartmentForm";
import { IssueForm } from "./IssueForm";
import { HeatmapFilter, RiskHeatmap } from "./RiskHeatmap";
import { RiskForm } from "./RiskForm";
import { Card, DataTable, DetailModal, ReadField } from "./ui";

type Tab = "risks" | "controls" | "issues" | "departments" | "assessments";

const TABS: { id: Tab; label: string }[] = [
  { id: "risks", label: "Risks" },
  { id: "controls", label: "Controls" },
  { id: "issues", label: "Issues" },
  { id: "departments", label: "Departments" },
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

export default function WorkspacePage() {
  const [tab, setTab] = useState<Tab>("risks");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [heatmapFilter, setHeatmapFilter] = useState<HeatmapFilter | null>(null);

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
  const [viewingAssessment, setViewingAssessment] = useState<RiskAssessment | null>(null);

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

  const entityName = (id: number | null) => entities.find((e) => e.id === id)?.name ?? "—";
  const riskName = (id: number | null) => risks.find((r) => r.id === id)?.name ?? "—";
  const controlName = (id: number | null) => controls.find((c) => c.id === id)?.name ?? "—";

  const filteredRisks = heatmapFilter
    ? risks.filter(
        (r) =>
          r.inherent_likelihood === heatmapFilter.likelihood &&
          r.inherent_impact === heatmapFilter.impact
      )
    : risks;

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
        <Link href="/" className="text-sm text-zinc-500 hover:underline">
          ← Home
        </Link>
      </div>

      {loadError && (
        <p className="mb-6 rounded-md border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {loadError}. Is the FastAPI backend running on port 8000?
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
                : `Risks (${risks.length})`
            }
          >
            <DataTable
              rows={filteredRisks}
              onRowClick={(r) => setViewingRisk(r)}
              onDelete={async (id) => {
                await apiDelete(`/api/v1/risks/${id}`);
                setRisks((prev) => prev.filter((r) => r.id !== id));
              }}
              columns={[
                { header: "Name", render: (r) => r.name },
                { header: "Entity", render: (r) => entityName(r.entity_id) },
                { header: "State", render: (r) => r.state },
                { header: "Assigned To", render: (r) => r.assigned_to ?? "—" },
                {
                  header: "Inherent",
                  render: (r) =>
                    r.inherent_likelihood && r.inherent_impact
                      ? r.inherent_likelihood * r.inherent_impact
                      : "—",
                },
                {
                  header: "Residual",
                  render: (r) =>
                    r.residual_likelihood && r.residual_impact
                      ? r.residual_likelihood * r.residual_impact
                      : "—",
                },
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
          <Card title={`Controls (${controls.length})`}>
            <DataTable
              rows={controls}
              onRowClick={(c) => setViewingControl(c)}
              onDelete={async (id) => {
                await apiDelete(`/api/v1/controls/${id}`);
                setControls((prev) => prev.filter((c) => c.id !== id));
              }}
              columns={[
                { header: "Name", render: (c) => c.name },
                { header: "Status", render: (c) => c.status },
                { header: "Entity", render: (c) => entityName(c.entity_id) },
                { header: "Mitigates", render: (c) => riskName(c.risk_id) },
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
          <Card title={`Issues (${issues.length})`}>
            <DataTable
              rows={issues}
              onRowClick={(i) => setViewingIssue(i)}
              onDelete={async (id) => {
                await apiDelete(`/api/v1/issues/${id}`);
                setIssues((prev) => prev.filter((i) => i.id !== id));
              }}
              columns={[
                { header: "Title", render: (i) => i.title },
                { header: "Priority", render: (i) => i.priority },
                { header: "State", render: (i) => i.state },
                { header: "Source", render: (i) => i.source },
                { header: "Related Risk", render: (i) => riskName(i.risk_id) },
                { header: "Related Control", render: (i) => controlName(i.control_id) },
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
              onDelete={async (id) => {
                await apiDelete(`/api/v1/departments/${id}`);
                setDepartments((prev) => prev.filter((d) => d.id !== id));
              }}
              columns={[
                { header: "Name", render: (d) => d.name },
                { header: "Manager", render: (d) => d.manager_id ?? "—" },
                { header: "Cost Center", render: (d) => d.cost_center ?? "—" },
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
            <DataTable
              rows={assessments}
              onRowClick={(a) => setViewingAssessment(a)}
              columns={[
                { header: "Risk", render: (a) => riskName(a.risk_id) },
                { header: "Assessor", render: (a) => a.assessor_id ?? "—" },
                { header: "State", render: (a) => a.state },
                { header: "Score", render: (a) => a.score ?? "—" },
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
              <div className="sm:col-span-2">
                <ReadField label="Description" value={r.description} />
              </div>
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
              <div className="sm:col-span-2">
                <ReadField label="Description" value={c.description} />
              </div>
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
