import { useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Submission } from "../api/types";
import { Panel, Spinner } from "./ui";
import { ProofCard } from "./ProofCard";

// Live grading verdict, with per-check evidence and an optional post-task
// AI review once the task passes.
export function GradePanel({
  submission,
  taskId,
  graderImplemented,
}: {
  submission: Submission | null;
  taskId: string;
  graderImplemented: boolean;
}) {
  if (!submission) return null;
  const running = submission.status === "queued" || submission.status === "running";

  return (
    <Panel
      className={
        submission.status === "passed"
          ? "border-phosphor/50 shadow-glow"
          : submission.status === "failed"
            ? "border-signal-red/40"
            : ""
      }
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="label mb-0">Grading result</h2>
        <Verdict status={submission.status} score={submission.score} />
      </div>

      {running && (
        <div className="flex items-center gap-3 py-2">
          <Spinner label={submission.status === "queued" ? "queued for the emulator…" : "running on the emulator…"} />
        </div>
      )}

      {submission.evidence && (
        <p className="rounded-md bg-ink-900/70 px-3 py-2 font-mono text-xs text-zinc-300">
          {submission.evidence}
        </p>
      )}

      {submission.checks.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {submission.checks.map((c, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className={c.passed ? "text-phosphor" : "text-signal-red"}>
                {c.passed ? "✓" : "✕"}
              </span>
              <span className="text-zinc-300">
                {c.name}
                {c.detail && <span className="text-zinc-600"> — {c.detail}</span>}
              </span>
            </li>
          ))}
        </ul>
      )}

      {submission.error && (
        <p className="mt-3 font-mono text-xs text-signal-amber">{submission.error}</p>
      )}

      {submission.status === "passed" && <ProofCard submissionId={submission.id} />}

      {submission.status === "passed" && graderImplemented && (
        <ReviewBlock taskId={taskId} />
      )}
    </Panel>
  );
}

function Verdict({ status, score }: { status: Submission["status"]; score: number }) {
  if (status === "passed")
    return <span className="font-mono text-sm font-bold text-phosphor">PASS · {score} pts</span>;
  if (status === "failed")
    return <span className="font-mono text-sm font-bold text-signal-red">FAIL</span>;
  if (status === "error")
    return <span className="font-mono text-sm font-bold text-signal-amber">ERROR</span>;
  return <span className="font-mono text-sm text-signal-cyan">{status}</span>;
}

function ReviewBlock({ taskId }: { taskId: string }) {
  const [review, setReview] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  async function getReview() {
    setBusy(true);
    setNote("");
    try {
      const r = await api.mentorReview(taskId);
      setReview(r.review);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setNote("Add your AI key in Settings to get a remediation review.");
      } else {
        setNote(e instanceof Error ? e.message : "Review failed");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-4 border-t border-ink-500/50 pt-3">
      {!review && (
        <button className="btn-ghost text-xs" onClick={getReview} disabled={busy}>
          {busy ? "thinking…" : "✦ AI remediation review"}
        </button>
      )}
      {note && <p className="mt-2 font-mono text-xs text-signal-amber">{note}</p>}
      {review && (
        <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">{review}</p>
      )}
    </div>
  );
}
