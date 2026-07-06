import { useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { EvidenceItem, Submission } from "../api/types";
import { Panel, Spinner } from "./ui";
import { ProofCard } from "./ProofCard";
import { GradingConsole } from "./GradingConsole";

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

      <GradingConsole submissionId={submission.id} />

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

      {submission.evidence_bundle?.length > 0 && (
        <EvidenceBundle items={submission.evidence_bundle} />
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

// The proof-of-technique flight recorder: the structured artifacts (baseline vs
// hooked logcat, frida trace, timeline) that prove the technique actually took
// effect — not just that a flag string matched.
function EvidenceBundle({ items }: { items: EvidenceItem[] }) {
  const [open, setOpen] = useState<number | null>(0);
  const icon: Record<string, string> = {
    log: "▤",
    trace: "↯",
    timeline: "⋮",
    note: "✎",
    network: "⇄",
  };
  return (
    <div className="mt-3 rounded-md border border-signal-cyan/30">
      <div className="border-b border-signal-cyan/20 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-signal-cyan">
        ✦ evidence bundle · proof of technique
      </div>
      <ul>
        {items.map((it, i) => (
          <li key={i} className="border-t border-ink-500/40 first:border-t-0">
            <button
              className="flex w-full items-center gap-2 px-3 py-2 text-left font-mono text-[11px] text-zinc-300 hover:text-phosphor"
              onClick={() => setOpen(open === i ? null : i)}
            >
              <span className="text-signal-cyan">{icon[it.kind] ?? "•"}</span>
              <span className="flex-1 truncate">{it.label}</span>
              <span className="text-zinc-600">{open === i ? "−" : "+"}</span>
            </button>
            {open === i && (
              <pre className="max-h-56 overflow-auto border-t border-ink-500/40 bg-ink-900/90 px-3 py-2 font-mono text-[10.5px] leading-relaxed text-zinc-400">
                {it.content}
              </pre>
            )}
          </li>
        ))}
      </ul>
    </div>
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
