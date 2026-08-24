"use client";

import { Risk } from "@/lib/api";

const LIKELIHOOD_LEVELS = [5, 4, 3, 2, 1]; // rows, top = highest likelihood
const IMPACT_LEVELS = [1, 2, 3, 4, 5]; // columns, left = lowest impact

export interface HeatmapFilter {
  likelihood: number;
  impact: number;
}

function cellColor(count: number, likelihood: number, impact: number) {
  if (count === 0) return "bg-zinc-50 text-zinc-300 dark:bg-zinc-900 dark:text-zinc-700";
  const score = likelihood * impact;
  if (score >= 20) return "bg-red-600 text-white";
  if (score >= 12) return "bg-orange-500 text-white";
  if (score >= 6) return "bg-yellow-400 text-zinc-900";
  return "bg-green-500 text-white";
}

export function RiskHeatmap({
  risks,
  selected,
  onSelectCell,
}: {
  risks: Risk[];
  selected: HeatmapFilter | null;
  onSelectCell: (cell: HeatmapFilter | null) => void;
}) {
  const countFor = (likelihood: number, impact: number) =>
    risks.filter((r) => r.inherent_likelihood === likelihood && r.inherent_impact === impact)
      .length;

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Risk Heatmap</h3>
          <p className="text-xs text-zinc-500">Inherent Likelihood × Impact — click a cell to filter</p>
        </div>
        {selected && (
          <button
            onClick={() => onSelectCell(null)}
            className="text-xs font-medium text-zinc-500 hover:underline"
          >
            Clear filter
          </button>
        )}
      </div>
      <div className="flex gap-2">
        <div className="flex flex-col justify-between py-0.5 text-xs font-medium text-zinc-500">
          {LIKELIHOOD_LEVELS.map((l) => (
            <div key={l} className="flex h-11 items-center">
              {l}
            </div>
          ))}
        </div>
        <div className="flex-1">
          <div className="grid grid-cols-5 gap-1">
            {LIKELIHOOD_LEVELS.map((likelihood) =>
              IMPACT_LEVELS.map((impact) => {
                const count = countFor(likelihood, impact);
                const isSelected = selected?.likelihood === likelihood && selected?.impact === impact;
                return (
                  <button
                    key={`${likelihood}-${impact}`}
                    type="button"
                    onClick={() => onSelectCell(isSelected ? null : { likelihood, impact })}
                    title={`Likelihood ${likelihood} × Impact ${impact}: ${count} risk(s)`}
                    className={`flex h-11 items-center justify-center rounded-md text-sm font-semibold transition ${cellColor(
                      count,
                      likelihood,
                      impact
                    )} ${
                      isSelected
                        ? "ring-2 ring-zinc-900 ring-offset-2 dark:ring-white"
                        : "hover:opacity-80"
                    }`}
                  >
                    {count}
                  </button>
                );
              })
            )}
          </div>
          <div className="mt-1 grid grid-cols-5 gap-1 text-center text-xs font-medium text-zinc-500">
            {IMPACT_LEVELS.map((i) => (
              <div key={i}>{i}</div>
            ))}
          </div>
          <p className="mt-1 text-center text-xs text-zinc-400">Impact →</p>
        </div>
      </div>
    </div>
  );
}
