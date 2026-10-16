import { useEffect, useRef, useState } from "react";
import { api } from "../api/endpoints";
import type { TaskManageView, TaskUpdate } from "../api/types";
import { ErrorText, Modal, PageHeader, Panel, Skeleton } from "../components/ui";

export function InstructorPage() {
  const [tasks, setTasks] = useState<TaskManageView[] | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

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

  async function uploadApk(id: string, file: File) {
    setError("");
    setBusyId(id);
    try {
      const updated = await api.instructorUploadApk(id, file);
      setTasks((ts) => (ts ? ts.map((t) => (t.id === id ? updated : t)) : ts));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusyId(null);
    }
  }

  async function removeTask(id: string) {
    setError("");
    setBusyId(id);
    try {
      await api.instructorDeleteTask(id);
      setTasks((ts) => (ts ? ts.filter((t) => t.id !== id) : ts));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
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
      <div className="flex items-start justify-between gap-3">
        <PageHeader
          eyebrow="instructor"
          title="Tasks"
          subtitle="Publish, hide, and edit tasks (presentation, step-by-step hints/solution, and the server-side answer key). Author new data-driven tasks with an uploaded APK. Device-driven graders (frida/network) still live in the repo. Your edits survive a re-seed."
        />
        <button className="btn-primary btn-sm shrink-0" onClick={() => setCreating(true)}>
          + New task
        </button>
      </div>
      {error && <ErrorText>{error}</ErrorText>}

      <Panel className="space-y-2 p-3">
        {tasks.map((t) => (
          <div key={t.id} className="rounded-lg border border-ink-700/60 bg-ink-900/40 p-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-2xs text-zinc-500">
                M{t.module}·{t.order_index}
              </span>
              <span className="flex-1 truncate text-sm text-zinc-100">{t.title}</span>
              {t.source === "authored" && (
                <span className="font-mono text-2xs text-signal-violet" title="instructor-authored">
                  authored
                </span>
              )}
              {t.instructor_edited && t.source !== "authored" && (
                <span className="font-mono text-2xs text-amber-400" title="edited by an instructor">
                  edited
                </span>
              )}
              <span className="font-mono text-2xs text-zinc-500">{t.success_type}</span>
              <span
                className="font-mono text-2xs text-zinc-600"
                title="challenge materials (uploaded or committed)"
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
            {editing === t.id && (
              <EditForm
                task={t}
                busy={busyId === t.id}
                onSave={patch}
                onUploadApk={uploadApk}
                onDelete={removeTask}
              />
            )}
          </div>
        ))}
      </Panel>

      {creating && (
        <NewTaskModal
          onClose={() => setCreating(false)}
          onCreated={(t) => {
            setTasks((ts) => (ts ? [...ts, t] : [t]));
            setCreating(false);
            setEditing(t.id);
          }}
        />
      )}
    </div>
  );
}

function EditForm({
  task,
  busy,
  onSave,
  onUploadApk,
  onDelete,
}: {
  task: TaskManageView;
  busy: boolean;
  onSave: (id: string, body: TaskUpdate) => void;
  onUploadApk: (id: string, file: File) => void;
  onDelete: (id: string) => void;
}) {
  const [title, setTitle] = useState(task.title);
  const [difficulty, setDifficulty] = useState(task.difficulty);
  const [time, setTime] = useState(task.time_estimate_min);
  const [objective, setObjective] = useState(task.objective);
  const [expected, setExpected] = useState(task.expected_value);
  const [h1, setH1] = useState(task.hints.h1 ?? "");
  const [h2, setH2] = useState(task.hints.h2 ?? "");
  const [h3, setH3] = useState(task.hints.h3 ?? "");
  const [solution, setSolution] = useState(task.hints.solution ?? "");
  const fileRef = useRef<HTMLInputElement | null>(null);

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
          expected_value: expected,
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

      <div>
        <label className="label" htmlFor={`exp-${task.id}`}>
          Expected value / flag (server-side answer key)
        </label>
        <input
          id={`exp-${task.id}`}
          className="input font-mono"
          placeholder="leave blank to use the on-disk grader"
          value={expected}
          onChange={(e) => setExpected(e.target.value)}
        />
        <p className="mt-1 font-mono text-2xs text-zinc-600">
          Overrides grader/expected.json. For flag / static_assert / network tasks. Never shown to
          learners.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dashed border-ink-400 bg-ink-900/40 px-4 py-3">
        <span className="label mb-0 text-zinc-300">Target APK</span>
        <span className="font-mono text-2xs text-zinc-500">
          {task.has_target_apk ? "present" : "none"}
        </span>
        <input
          ref={fileRef}
          type="file"
          accept=".apk,application/vnd.android.package-archive"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUploadApk(task.id, f);
            e.target.value = "";
          }}
        />
        <button
          type="button"
          className="btn-ghost btn-sm"
          disabled={busy}
          onClick={() => fileRef.current?.click()}
        >
          {busy ? "uploading…" : task.has_target_apk ? "Replace APK" : "Upload APK"}
        </button>
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

      <div className="flex items-center justify-between">
        <button className="btn-primary" disabled={busy}>
          {busy ? "saving…" : "Save changes"}
        </button>
        {task.source === "authored" && (
          <button
            type="button"
            className="btn-ghost btn-sm text-signal-red hover:border-signal-red/60 hover:text-signal-red"
            disabled={busy}
            onClick={() => onDelete(task.id)}
          >
            Delete task
          </button>
        )}
      </div>
    </form>
  );
}

function NewTaskModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (t: TaskManageView) => void;
}) {
  const [id, setId] = useState("");
  const [title, setTitle] = useState("");
  const [module, setModule] = useState("0");
  const [domain, setDomain] = useState("foundations");
  const [successType, setSuccessType] = useState<"flag" | "static_assert">("flag");
  const [objective, setObjective] = useState("");
  const [expected, setExpected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const field = successType === "flag" ? "flag" : "value";
      const t = await api.instructorCreateTask({
        id: id.trim(),
        title: title.trim(),
        module: module.trim(),
        domain: domain.trim(),
        success_type: successType,
        objective: objective.trim(),
        expected_value: expected.trim(),
        submission_schema: { [field]: "string" },
      });
      onCreated(t);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create task");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="New task" onClose={onClose}>
      <p className="text-sm text-zinc-400">
        Author a data-driven task: the learner submits a value and the grader compares it to your
        answer key. Add a target APK after creating. Device-driven (frida/network) graders need
        code in the repo.
      </p>
      <form className="space-y-3" onSubmit={submit}>
        <div className="flex flex-wrap gap-3">
          <div className="min-w-[12rem] flex-1">
            <label className="label" htmlFor="nt-id">Task id (slug)</label>
            <input id="nt-id" className="input font-mono" placeholder="200-my-new-lab" required value={id} onChange={(e) => setId(e.target.value)} />
          </div>
          <div className="w-24">
            <label className="label" htmlFor="nt-module">Module</label>
            <input id="nt-module" className="input" value={module} onChange={(e) => setModule(e.target.value)} />
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="min-w-[12rem] flex-1">
            <label className="label" htmlFor="nt-title">Title</label>
            <input id="nt-title" className="input" required value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="w-40">
            <label className="label" htmlFor="nt-domain">Domain</label>
            <input id="nt-domain" className="input font-mono" value={domain} onChange={(e) => setDomain(e.target.value)} />
          </div>
          <div className="w-40">
            <label className="label" htmlFor="nt-type">Grading type</label>
            <select id="nt-type" className="input" value={successType} onChange={(e) => setSuccessType(e.target.value as "flag" | "static_assert")}>
              <option value="flag">flag</option>
              <option value="static_assert">static_assert</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label" htmlFor="nt-obj">Objective</label>
          <textarea id="nt-obj" className="input min-h-[5rem] font-mono text-xs" value={objective} onChange={(e) => setObjective(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="nt-exp">Expected value / flag (answer key)</label>
          <input id="nt-exp" className="input font-mono" required value={expected} onChange={(e) => setExpected(e.target.value)} />
        </div>
        {error && <ErrorText>{error}</ErrorText>}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "creating…" : "Create task (draft)"}
        </button>
      </form>
    </Modal>
  );
}
