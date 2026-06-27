import { useState } from "react";
import type { TaskDetail } from "../api/types";
import { ErrorText } from "./ui";

// Maps a task's success_type to the payload the backend expects.
function buildPayload(task: TaskDetail, value: string): Record<string, unknown> {
  switch (task.success_type) {
    case "flag":
      return { flag: value };
    case "static_assert":
      return { value };
    case "frida_assert":
      return { script: value };
    case "network_assert":
      return { value, note: value };
    default:
      return { value };
  }
}

const PLACEHOLDER: Record<TaskDetail["success_type"], string> = {
  flag: "FLAG{...}",
  static_assert: "the value you recovered (e.g. an API key)",
  frida_assert: "// your Frida script\nJava.perform(function () { ... });",
  network_assert: "the value you intercepted (e.g. the captured token)",
};

export function SubmitForm({
  task,
  onSubmit,
}: {
  task: TaskDetail;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isScript = task.success_type === "frida_assert";

  if (task.grader_status !== "implemented") {
    return (
      <p className="rounded-md border border-signal-amber/30 bg-signal-amber/5 px-3 py-2 text-sm text-signal-amber">
        This task is scaffolded — its grader isn't implemented yet. Try one of the ★ reference
        tasks to see live grading.
      </p>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!value.trim()) {
      setError("Enter something to submit.");
      return;
    }
    setBusy(true);
    try {
      await onSubmit(buildPayload(task, value));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      {isScript ? (
        <textarea
          className="input min-h-[160px] font-mono text-xs leading-relaxed"
          spellCheck={false}
          placeholder={PLACEHOLDER[task.success_type]}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      ) : (
        <input
          className="input font-mono"
          placeholder={PLACEHOLDER[task.success_type]}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      )}
      {error && <ErrorText>{error}</ErrorText>}
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] text-zinc-600">
          {task.success_type === "network_assert"
            ? "the runner proxies the emulator and triggers the app for you"
            : "graded live on a real Android emulator"}
        </span>
        <button className="btn-primary" disabled={busy}>
          {busy ? "submitting…" : "Submit & grade"}
        </button>
      </div>
    </form>
  );
}
