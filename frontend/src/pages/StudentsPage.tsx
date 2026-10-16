import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { RosterEntry } from "../api/types";
import { ErrorText, PageHeader, Panel, Skeleton } from "../components/ui";
import { StatsModal } from "../components/StatsModal";

export function StudentsPage() {
  const [roster, setRoster] = useState<RosterEntry[] | null>(null);
  const [error, setError] = useState("");
  const [statsUserId, setStatsUserId] = useState<number | null>(null);

  useEffect(() => {
    api.roster().then(setRoster).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        eyebrow="staff"
        title="Students"
        subtitle="Every learner and their progress. Click a row to see the full per-domain breakdown."
      />
      {error && <ErrorText>{error}</ErrorText>}

      {!roster ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <Panel className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-500/60 text-left font-mono text-2xs uppercase text-zinc-500">
                <th className="px-4 py-3">Learner</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Passed</th>
                <th className="px-4 py-3">Score</th>
              </tr>
            </thead>
            <tbody>
              {roster.map((r) => (
                <tr
                  key={r.id}
                  className="cursor-pointer border-b border-ink-700/50 last:border-0 hover:bg-ink-700/40"
                  onClick={() => setStatsUserId(r.id)}
                >
                  <td className="px-4 py-3">
                    <div className="text-zinc-100">{r.display_name}</div>
                    <div className="font-mono text-xs text-zinc-500">{r.email}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-zinc-400">{r.role}</td>
                  <td className="px-4 py-3 font-mono text-xs text-phosphor">
                    {r.tasks_passed}/{r.tasks_total}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-zinc-300">{r.total_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}

      {statsUserId !== null && (
        <StatsModal userId={statsUserId} onClose={() => setStatsUserId(null)} />
      )}
    </div>
  );
}
