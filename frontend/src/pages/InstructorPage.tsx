import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { TaskManageView, TaskUpdate } from "../api/types";
import { ErrorText, PageHeader, Panel, Skeleton } from "../components/ui";

export function InstructorPage() {
  const [tasks, setTasks] = useState<TaskManageView[] | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  function load() {
    api.instructorListTasks().then(setTasks).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function patch(id: string, body: TaskUpdate) {
    setError("");
    setBusyId(id);
    try {
      const updated = await api.instructorUpdateTask(id, body);
      setTasks((ts) => (ts ? ts.map((t) => (t.id === id ? updated : t)) : ts));
      setEditing(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusyId(null);
    }
  }

  if (!tasks)
    return (
      <div className="mx-auto max-w-4xl space-y-6" role="status" aria-label="loading tasks">
        <Skeleton className="h-7 w-40" />
        <div className="panel space-y-3 p-5">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    );

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        eyebrow="instructor"
        title="Tasks"
        subtitle="Publish or hide tasks and edit their learner-facing presentation. Graders, hints, and submission schemas live in the task package on disk and aren't edited here. Your edits survive a re-seed."
      />
      {error && <ErrorText>{error}</ErrorText>}

      <Panel className="space-y-2 p-3">
        {tasks.map((t) => (
          <div key={t.id} className="rounded-lg border border-ink-700/60 bg-ink-900/40 p-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-2xs text-zinc-500">
                M{t.module}·{t.order_index}
              </span>
              <span className="flex-1 truncate text-sm text-zinc-100">{t.title}</span>
              {t.instructor_edited && (
                <span className="font-mono text-2xs text-amber-400" title="edited by an instructor">
                  edited
                </span>
              )}
              <span className="font-mono text-2xs text-zinc-500">{t.success_type}</span>
              <span
                className="font-mono text-2xs text-zinc-600"
                title="committed challenge materials"
              >
                {t.has_target_apk ? "apk" : "no-apk"} · {t.artifact_count} files
              </span>
              <button
                className={`btn-ghost btn-sm ${t.is_published ? "text-phosphor" : "text-zinc-500"}`}
                disabled={busyId === t.id}
                onClick={() => patch(t.id, { is_published: !t.is_published })}
              >
                {t.is_published ? "published" : "hidden"}
              </button>
              <button
                className="btn-ghost btn-sm"
                onClick={() => setEditing(editing === t.id ? null : t.id)}
              >
                {editing === t.id ? "close" : "edit"}
              </button>
            </div>
            {editing === t.id && <EditForm task={t} busy={busyId === t.id} onSave={patch} />}
          </div>
        ))}
      </Panel>
    </div>
  );
}

function EditForm({
  task,
  busy,
  onSave,
}: {
  task: TaskManageView;
  busy: boolean;
  onSave: (id: string, body: TaskUpdate) => void;
}) {
  const [title, setTitle] = useState(task.title);
  const [difficulty, setDifficulty] = useState(task.difficulty);
  const [time, setTime] = useState(task.time_estimate_min);
  const [objective, setObjective] = useState(task.objective);
  const [h1, setH1] = useState(task.hints.h1 ?? "");
  const [h2, setH2] = useState(task.hints.h2 ?? "");
  const [h3, setH3] = useState(task.hints.h3 ?? "");
  const [solution, setSolution] = useState(task.hints.solution ?? "");

  return (
    <form
      className="mt-3 space-y-3 border-t border-ink-700/60 pt-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSave(task.id, {
          title,
          difficulty,
          time_estimate_min: time,
          objective,
          hints: { h1, h2, h3, solution },
        });
      }}
    >
      <div className="flex flex-wrap gap-3">
        <div className="min-w-[14rem] flex-1">
          <label className="label" htmlFor={`title-${task.id}`}>
            Title
          </label>
          <input
            id={`title-${task.id}`}
            className="input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div className="w-28">
          <label className="label" htmlFor={`diff-${task.id}`}>
            Difficulty
          </label>
          <input
            id={`diff-${task.id}`}
            className="input"
            type="number"
            min={1}
            max={5}
            value={difficulty}
            onChange={(e) => setDifficulty(Number(e.target.value))}
          />
        </div>
        <div className="w-28">
          <label className="label" htmlFor={`time-${task.id}`}>
            Minutes
          </label>
          <input
            id={`time-${task.id}`}
            className="input"
            type="number"
            min={1}
            max={600}
            value={time}
            onChange={(e) => setTime(Number(e.target.value))}
          />
        </div>
      </div>
      <div>
        <label className="label" htmlFor={`obj-${task.id}`}>
          Objective
        </label>
        <textarea
          id={`obj-${task.id}`}
          className="input min-h-[7rem] font-mono text-xs"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
        />
      </div>

      <details className="rounded-lg border border-dashed border-ink-400 bg-ink-900/40 px-4 py-3">
        <summary className="label mb-0 cursor-pointer select-none text-zinc-300">
          Step-by-step answer key (hints and solution)
        </summary>
        <p className="mt-2 text-xs text-zinc-500">
          Markdown. Hints are revealed tier by tier and lower the learner's score; the solution
          unlocks last. Edits here survive a re-seed.
        </p>
        <div className="mt-3 space-y-3">
          {([
            ["h1", "Hint 1", h1, setH1],
            ["h2", "Hint 2", h2, setH2],
            ["h3", "Hint 3", h3, setH3],
            ["solution", "Solution", solution, setSolution],
          ] as const).map(([key, label, val, set]) => (
            <div key={key}>
              <label className="label" htmlFor={`${key}-${task.id}`}>
                {label}
              </label>
              <textarea
                id={`${key}-${task.id}`}
                className="input min-h-[5rem] font-mono text-xs"
                value={val}
                onChange={(e) => set(e.target.value)}
              />
            </div>
          ))}
        </div>
      </details>

      <button className="btn-primary" disabled={busy}>
        {busy ? "saving…" : "Save changes"}
      </button>
    </form>
  );
}
