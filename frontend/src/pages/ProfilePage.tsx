import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { ProfileStats } from "../api/types";
import { ErrorText, PageHeader, Panel, Skeleton } from "../components/ui";

export function ProfilePage() {
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.stats().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!stats) return <ProfileSkeleton />;

  const overall = stats.tasks_total ? Math.round((stats.tasks_passed / stats.tasks_total) * 100) : 0;

  const tiles = [
    { label: "Tasks cleared", value: `${stats.tasks_passed}`, sub: `of ${stats.tasks_total}`, accent: true },
    { label: "Total score", value: `${stats.total_score}`, sub: "pts", accent: true },
    { label: "Attempts", value: `${stats.total_attempts}`, sub: "submissions" },
    { label: "Hints used", value: `${stats.total_hints_used}`, sub: "score deductions" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="learner profile"
        title={stats.display_name}
        subtitle="Your mastery across the curriculum."
        aside={
          <div className="text-right">
            <p className="eyebrow">curriculum</p>
            <p className="font-mono text-2xl font-bold text-phosphor">
              {overall}
              <span className="text-sm font-medium text-zinc-500">%</span>
            </p>
          </div>
        }
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {tiles.map((t) => (
          <Panel key={t.label} className="relative overflow-hidden">
            <p className="eyebrow">{t.label}</p>
            <p className={`mt-2 font-mono text-3xl font-bold tracking-tight ${t.accent ? "text-phosphor" : "text-zinc-100"}`}>
              {t.value}
              <span className="ml-1.5 text-xs font-medium text-zinc-500">{t.sub}</span>
            </p>
          </Panel>
        ))}
      </div>

      <Panel>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="label mb-0">Domain mastery</h2>
          <span className="font-mono text-2xs uppercase text-zinc-500">MASVS domains</span>
        </div>
        <ul className="space-y-4">
          {stats.domains.map((d) => {
            const pct = d.tasks_total ? Math.round((d.tasks_passed / d.tasks_total) * 100) : 0;
            const done = d.tasks_total > 0 && d.tasks_passed === d.tasks_total;
            return (
              <li key={d.domain}>
                <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="flex items-center gap-2 font-mono text-zinc-100">
                    {done && <span className="text-phosphor" aria-label="domain complete">✓</span>}
                    {d.domain}
                  </span>
                  <span className="font-mono text-2xs uppercase text-zinc-400">
                    <span className="text-zinc-200">{d.tasks_passed}</span>/{d.tasks_total}
                    <span className="mx-2 text-zinc-600">·</span>avg {d.avg_score} pts
                    <span className="mx-2 text-zinc-600">·</span>max diff {d.highest_difficulty_cleared}/5
                  </span>
                </div>
                <div className="relative h-2 overflow-hidden rounded-full bg-ink-600" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={`${d.domain} ${pct}%`}>
                  <div
                    className={`h-full rounded-full transition-[width] duration-700 ${
                      done ? "bg-phosphor shadow-[0_0_10px_rgba(57,255,139,0.6)]" : "bg-gradient-to-r from-phosphor-dim to-phosphor/80"
                    }`}
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

function ProfileSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="loading profile">
      <div className="space-y-2">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-7 w-56" />
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="panel space-y-3 p-5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-16" />
          </div>
        ))}
      </div>
      <div className="panel space-y-4 p-5">
        <Skeleton className="h-3 w-32" />
        {[0, 1, 2].map((i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-3.5 w-40" />
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
