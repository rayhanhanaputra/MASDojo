import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { ProfileStats, TaskStat } from "../api/types";
import { ErrorText, Modal, Skeleton } from "./ui";

/** A modal showing one user's comprehensive progress stats, fetched by id. */
export function StatsModal({ userId, onClose }: { userId: number; onClose: () => void }) {
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"summary" | "tasks">("summary");

  useEffect(() => {
    api.userStats(userId).then(setStats).catch((e) => setError(e.message));
  }, [userId]);

  return (
    <Modal title={stats ? `${stats.display_name} · stats` : "User stats"} onClose={onClose}>
      {error && <ErrorText>{error}</ErrorText>}
      {!stats ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="space-y-4">
          <div className="flex gap-1 border-b border-ink-500/50">
            {(["summary", "tasks"] as const).map((t) => (
              <button
                key={t}
                className={`rounded-t-md px-3 py-1.5 text-sm ${
                  tab === t ? "border-b-2 border-phosphor text-phosphor" : "text-zinc-400"
                }`}
                onClick={() => setTab(t)}
              >
                {t === "summary" ? "Summary" : `Tasks (${stats.tasks.length})`}
              </button>
            ))}
          </div>
          {tab === "summary" ? <Summary s={stats} /> : <TasksTab tasks={stats.tasks} />}
        </div>
      )}
    </Modal>
  );
}

function Summary({ s }: { s: ProfileStats }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-2 text-center">
        <Stat label="completion" value={`${s.completion_pct}%`} sub={`${s.tasks_passed}/${s.tasks_total}`} />
        <Stat label="score" value={String(s.total_score)} />
        <Stat label="pass rate" value={`${s.pass_rate}%`} sub={`of ${s.tasks_attempted} tried`} />
        <Stat label="attempts" value={String(s.total_attempts)} sub={`${s.avg_attempts_per_pass}/pass`} />
        <Stat label="hints used" value={String(s.total_hints_used)} />
        <Stat label="hardest cleared" value={s.highest_difficulty_cleared ? `${s.highest_difficulty_cleared}/5` : "-"} />
      </div>

      <div className="grid grid-cols-2 gap-2 font-mono text-xs text-zinc-400">
        <Line k="avg solve time" v={s.avg_time_to_solve_min ? `${s.avg_time_to_solve_min} min` : "-"} />
        <Line k="MASVS covered" v={s.masvs_covered.length ? String(s.masvs_covered.length) : "-"} />
        <Line k="first active" v={fmtDate(s.first_active)} />
        <Line k="last active" v={fmtDate(s.last_active)} />
      </div>

      <div>
        <p className="label">By module</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-xs">
          {s.modules.map((m) => {
            const pct = m.tasks_total ? Math.round((100 * m.tasks_passed) / m.tasks_total) : 0;
            return (
              <div key={m.module} className="flex items-center gap-2">
                <span className="w-8 text-zinc-500">M{m.module}</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink-700">
                  <div className="h-full rounded-full bg-phosphor" style={{ width: `${pct}%` }} />
                </div>
                <span className="w-10 text-right text-zinc-400">
                  {m.tasks_passed}/{m.tasks_total}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <p className="label">By domain</p>
        <ul className="divide-y divide-ink-700/50 font-mono text-xs">
          {s.domains.map((d) => (
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
  );
}

const STATUS_DOT: Record<TaskStat["status"], string> = {
  passed: "bg-phosphor",
  attempted: "bg-signal-amber",
  not_started: "bg-zinc-700",
};

function TasksTab({ tasks }: { tasks: TaskStat[] }) {
  return (
    <div className="max-h-[22rem] space-y-1 overflow-y-auto pr-1">
      {tasks.map((t) => (
        <div
          key={t.task_id}
          className="flex items-center gap-3 rounded-md border border-ink-700/50 bg-ink-900/40 px-3 py-2"
        >
          <span aria-hidden className={`h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[t.status]}`} />
          <span className="font-mono text-2xs text-zinc-600">M{t.module}</span>
          <span className="flex-1 truncate text-sm text-zinc-200">{t.title}</span>
          <span className="font-mono text-2xs text-zinc-500">
            {t.attempts > 0 ? `${t.attempts} try` : "-"}
          </span>
          {t.hint_tier_used > 0 && (
            <span className="font-mono text-2xs text-amber-400">h{t.hint_tier_used}</span>
          )}
          <span
            className={`w-10 text-right font-mono text-xs ${
              t.status === "passed" ? "text-phosphor" : "text-zinc-600"
            }`}
          >
            {t.status === "passed" ? t.best_score : "-"}
          </span>
        </div>
      ))}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-ink-400 bg-ink-900/50 px-3 py-2.5">
      <p className="font-mono text-lg font-bold text-phosphor">{value}</p>
      <p className="font-mono text-2xs uppercase text-zinc-500">{label}</p>
      {sub && <p className="font-mono text-2xs text-zinc-600">{sub}</p>}
    </div>
  );
}

function Line({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between rounded border border-ink-700/50 px-2 py-1">
      <span className="text-zinc-500">{k}</span>
      <span className="text-zinc-300">{v}</span>
    </div>
  );
}

function fmtDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString();
}
