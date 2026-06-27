import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { ProfileStats } from "../api/types";
import { ErrorText, Panel, Spinner } from "../components/ui";

export function ProfilePage() {
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!stats) return <Spinner label="loading stats…" />;

  const tiles = [
    { label: "Tasks cleared", value: `${stats.tasks_passed} / ${stats.tasks_total}` },
    { label: "Total score", value: stats.total_score },
    { label: "Attempts", value: stats.total_attempts },
    { label: "Hints used", value: stats.total_hints_used },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-100">{stats.display_name}</h1>
        <p className="mt-1 text-sm text-zinc-500">Your mastery across the curriculum.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {tiles.map((t) => (
          <Panel key={t.label} className="text-center">
            <p className="font-mono text-2xl font-bold text-phosphor">{t.value}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-zinc-500">{t.label}</p>
          </Panel>
        ))}
      </div>

      <Panel>
        <h2 className="label">Domain mastery</h2>
        <ul className="space-y-3">
          {stats.domains.map((d) => {
            const pct = d.tasks_total ? Math.round((d.tasks_passed / d.tasks_total) * 100) : 0;
            return (
              <li key={d.domain}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-mono text-zinc-300">{d.domain}</span>
                  <span className="font-mono text-xs text-zinc-500">
                    {d.tasks_passed}/{d.tasks_total} · avg {d.avg_score} pts · diff{" "}
                    {d.highest_difficulty_cleared}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-ink-600">
                  <div
                    className="h-full rounded-full bg-phosphor/70"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      </Panel>
    </div>
  );
}
