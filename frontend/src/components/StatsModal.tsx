import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { ProfileStats } from "../api/types";
import { ErrorText, Modal, Skeleton } from "./ui";

/** A modal showing one user's progress stats, fetched by id. Used by the admin
 * Users table and the staff Students roster. */
export function StatsModal({ userId, onClose }: { userId: number; onClose: () => void }) {
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.userStats(userId).then(setStats).catch((e) => setError(e.message));
  }, [userId]);

  return (
    <Modal title={stats ? `${stats.display_name} · stats` : "User stats"} onClose={onClose}>
      {error && <ErrorText>{error}</ErrorText>}
      {!stats ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-2 text-center">
            <Stat label="passed" value={`${stats.tasks_passed}/${stats.tasks_total}`} />
            <Stat label="score" value={String(stats.total_score)} />
            <Stat label="hints" value={String(stats.total_hints_used)} />
          </div>
          <div>
            <p className="label">By domain</p>
            <ul className="divide-y divide-ink-700/50 font-mono text-xs">
              {stats.domains.map((d) => (
                <li key={d.domain} className="flex items-center justify-between py-1.5">
                  <span className="text-zinc-300">{d.domain}</span>
                  <span className="text-zinc-500">
                    {d.tasks_passed}/{d.tasks_total} · avg {d.avg_score}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </Modal>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-ink-400 bg-ink-900/50 px-3 py-2.5">
      <p className="font-mono text-lg font-bold text-phosphor">{value}</p>
      <p className="font-mono text-2xs uppercase text-zinc-500">{label}</p>
    </div>
  );
}
