import { useState } from "react";
import type { TaskDetail } from "../api/types";
import { ErrorText, GRADER_META } from "./ui";

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
      return { value };
    default:
      return { value };
  }
}

const PLACEHOLDER: Record<TaskDetail["success_type"], string> = {
  flag: "FLAG{...}",
  static_assert: "the value you recovered (e.g. an API key)",
  frida_assert: "// your Frida script\nJava.perform(function () { ... });",
  network_assert: "the value you intercepted (e.g. the captured token)",
  patch_assert: "",
};

const FIELD_LABEL: Record<TaskDetail["success_type"], string> = {
  flag: "flag",
  static_assert: "recovered value",
  frida_assert: "frida script",
  network_assert: "intercepted value",
  patch_assert: "patched, re-signed APK",
};

export function SubmitForm({
  task,
  onSubmit,
  onSubmitApk,
}: {
  task: TaskDetail;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
  onSubmitApk?: (file: File) => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isScript = task.success_type === "frida_assert";
  const isPatch = task.success_type === "patch_assert";
  const meta = GRADER_META[task.success_type];

  if (task.grader_status !== "implemented") {
    return (
      <p className="flex items-start gap-2 rounded-md border border-signal-amber/30 bg-signal-amber/5 px-3 py-2.5 text-sm text-signal-amber">
        <span aria-hidden>⚠</span>
        <span>
          This task is scaffolded, its grader isn't implemented yet. Try one of the ★ reference
          tasks to see live grading.
        </span>
      </p>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isPatch) {
        if (!file) {
          setError("Choose your patched, re-signed APK to upload.");
          return;
        }
        await onSubmitApk?.(file);
      } else {
        if (!value.trim()) {
          setError("Enter something to submit.");
          return;
        }
        await onSubmit(buildPayload(task, value));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div>
        <label className="label flex items-center gap-2" htmlFor="submission-value">
          <span className={meta.text} aria-hidden>
            {meta.glyph}
          </span>
          {FIELD_LABEL[task.success_type]}
        </label>
        {isPatch ? (
          <input
            id="submission-value"
            type="file"
            accept=".apk,application/vnd.android.package-archive"
            className="input font-mono text-xs file:mr-3 file:rounded file:border-0 file:bg-ink-700 file:px-3 file:py-1.5 file:text-zinc-200"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        ) : isScript ? (
          <textarea
            id="submission-value"
            className="input min-h-[180px] font-mono text-xs leading-relaxed"
            spellCheck={false}
            placeholder={PLACEHOLDER[task.success_type]}
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        ) : (
          <input
            id="submission-value"
            className="input font-mono"
            placeholder={PLACEHOLDER[task.success_type]}
            value={value}
            spellCheck={false}
            autoComplete="off"
            onChange={(e) => setValue(e.target.value)}
          />
        )}
      </div>
      {error && <ErrorText>{error}</ErrorText>}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="font-mono text-2xs uppercase text-zinc-500">
          {task.success_type === "network_assert"
            ? "the runner proxies the emulator and triggers the app for you"
            : isPatch
              ? "the runner installs & runs your patched build to verify the unlock"
              : `graded live on a real Android emulator · ${meta.describe}`}
        </span>
        <button className="btn-primary" disabled={busy}>
          {busy ? "submitting…" : isPatch ? "Upload & grade" : "Submit & grade"}
          {!busy && <span aria-hidden>▶</span>}
        </button>
      </div>
    </form>
  );
}
