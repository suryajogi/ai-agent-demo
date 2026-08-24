"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import {
  apiGet,
  apiPost,
  AssessmentQuestion,
  Risk,
  RiskAssessment,
  RiskAssessmentWithResponses,
} from "@/lib/api";

type Answers = Record<number, { selected_value: number; justification: string }>;

const SCALE = [1, 2, 3, 4, 5];
const SCALE_LABELS: Record<number, string> = {
  1: "Strongly Disagree",
  2: "Disagree",
  3: "Neutral",
  4: "Agree",
  5: "Strongly Agree",
};

export default function AssessorPortalPage() {
  const [assessorId, setAssessorId] = useState("");
  const [identityInput, setIdentityInput] = useState("");
  const [assessments, setAssessments] = useState<RiskAssessment[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selected, setSelected] = useState<RiskAssessment | null>(null);
  const [risk, setRisk] = useState<Risk | null>(null);
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [answers, setAnswers] = useState<Answers>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<RiskAssessmentWithResponses | null>(null);

  useEffect(() => {
    if (!assessorId) return;
    apiGet<RiskAssessment[]>(`/api/v1/risk-assessments?assessor_id=${encodeURIComponent(assessorId)}`)
      .then((all) => {
        setAssessments(all.filter((a) => a.state !== "Completed"));
        setError(null);
      })
      .catch((err) => setError((err as Error).message));
  }, [assessorId]);

  async function openAssessment(assessment: RiskAssessment) {
    setSelected(assessment);
    setResult(null);
    setAnswers({});
    setError(null);
    try {
      const [riskData, questionData] = await Promise.all([
        assessment.risk_id ? apiGet<Risk>(`/api/v1/risks/${assessment.risk_id}`) : Promise.resolve(null),
        assessment.template_id
          ? apiGet<AssessmentQuestion[]>(`/api/v1/assessment-questions?template_id=${assessment.template_id}`)
          : Promise.resolve([]),
      ]);
      setRisk(riskData);
      setQuestions(questionData);
      const initial: Answers = {};
      questionData.forEach((q) => {
        initial[q.id] = { selected_value: 3, justification: "" };
      });
      setAnswers(initial);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const submitted = await apiPost<RiskAssessmentWithResponses>(
        `/api/v1/risk-assessments/${selected.id}/submit`,
        {
          answers: questions.map((q) => ({
            question_id: q.id,
            selected_value: answers[q.id]?.selected_value ?? 3,
            justification: answers[q.id]?.justification || null,
          })),
        }
      );
      setResult(submitted);
      setAssessments((prev) => (prev ?? []).filter((a) => a.id !== selected.id));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  function backToList() {
    setSelected(null);
    setRisk(null);
    setQuestions([]);
    setAnswers({});
    setResult(null);
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-2xl flex-col justify-center px-6 py-10">
      <p className="mb-1 text-center text-sm font-medium uppercase tracking-wide text-zinc-500">
        Interface B
      </p>
      <h1 className="mb-8 text-center text-2xl font-semibold tracking-tight">Assessor Portal</h1>

      {error && (
        <p className="mb-6 rounded-md border border-red-300 bg-red-50 px-4 py-2 text-center text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {!assessorId && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setAssessorId(identityInput.trim());
          }}
          className="mx-auto flex w-full max-w-sm flex-col gap-4 rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
        >
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-zinc-600 dark:text-zinc-400">Your assessor ID</span>
            <input
              required
              autoFocus
              className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900"
              placeholder="e.g. s.washington"
              value={identityInput}
              onChange={(e) => setIdentityInput(e.target.value)}
            />
          </label>
          <button
            type="submit"
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            View my assessments
          </button>
        </form>
      )}

      {assessorId && !selected && (
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <div className="mb-6 flex items-center justify-between">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Signed in as <span className="font-medium text-zinc-900 dark:text-zinc-100">{assessorId}</span>
            </p>
            <button onClick={() => setAssessorId("")} className="text-sm text-zinc-500 hover:underline">
              Switch user
            </button>
          </div>
          <h2 className="mb-4 text-lg font-semibold">Assigned Assessments</h2>
          {assessments === null && <p className="text-sm text-zinc-500">Loading…</p>}
          {assessments !== null && assessments.length === 0 && (
            <p className="text-sm text-zinc-500">No pending assessments assigned to you.</p>
          )}
          <ul className="flex flex-col gap-3">
            {(assessments ?? []).map((a) => (
              <li key={a.id}>
                <button
                  onClick={() => openAssessment(a)}
                  className="flex w-full items-center justify-between rounded-lg border border-zinc-200 px-4 py-3 text-left text-sm hover:border-zinc-400 dark:border-zinc-800 dark:hover:border-zinc-600"
                >
                  <span>Risk Assessment #{a.id}</span>
                  <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                    {a.state}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {assessorId && selected && !result && (
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <button onClick={backToList} className="mb-4 text-sm text-zinc-500 hover:underline">
            ← Back to my assessments
          </button>
          {risk && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold">{risk.name}</h2>
              {risk.description && (
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{risk.description}</p>
              )}
            </div>
          )}
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            {questions.map((q, idx) => (
              <fieldset key={q.id} className="border-t border-zinc-100 pt-4 dark:border-zinc-800">
                <legend className="mb-3 text-sm font-medium">
                  {idx + 1}. {q.question_text}
                </legend>
                <div className="grid grid-cols-5 gap-2">
                  {SCALE.map((value) => (
                    <label
                      key={value}
                      className={`flex cursor-pointer flex-col items-center gap-1 rounded-md border px-2 py-2 text-xs transition ${
                        answers[q.id]?.selected_value === value
                          ? "border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-900"
                          : "border-zinc-200 text-zinc-600 hover:border-zinc-400 dark:border-zinc-800 dark:text-zinc-400"
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${q.id}`}
                        value={value}
                        className="sr-only"
                        checked={answers[q.id]?.selected_value === value}
                        onChange={() =>
                          setAnswers((prev) => ({
                            ...prev,
                            [q.id]: { ...prev[q.id], selected_value: value, justification: prev[q.id]?.justification ?? "" },
                          }))
                        }
                      />
                      <span className="font-semibold">{value}</span>
                      <span className="text-center leading-tight">{SCALE_LABELS[value]}</span>
                    </label>
                  ))}
                </div>
                <input
                  className="mt-3 w-full rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none dark:border-zinc-800 dark:bg-zinc-900"
                  placeholder="Optional justification"
                  value={answers[q.id]?.justification ?? ""}
                  onChange={(e) =>
                    setAnswers((prev) => ({
                      ...prev,
                      [q.id]: { ...prev[q.id], justification: e.target.value },
                    }))
                  }
                />
              </fieldset>
            ))}
            <button
              type="submit"
              disabled={submitting || questions.length === 0}
              className="mt-2 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {submitting ? "Submitting…" : "Submit Assessment"}
            </button>
          </form>
        </div>
      )}

      {assessorId && selected && result && (
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">Submitted</p>
          <p className="mt-2 text-4xl font-semibold">{result.score}</p>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            Weighted risk score (1-5 scale) for {risk?.name ?? `Risk #${result.risk_id}`}
          </p>
          <button
            onClick={backToList}
            className="mt-6 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Back to my assessments
          </button>
        </div>
      )}

      <Link href="/" className="mt-8 text-center text-sm text-zinc-500 hover:underline">
        ← Home
      </Link>
    </div>
  );
}
