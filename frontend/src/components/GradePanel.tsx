import { useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { EvidenceItem, Submission } from "../api/types";
import { MentorMark, Panel, Spinner } from "./ui";
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
  const passed = submission.status === "passed";
  const failed = submission.status === "failed";

  const passCount = submission.checks.filter((c) => c.passed).length;

  return (
    <Panel
      className={`animate-rise ${
        passed
          ? "border-phosphor/50"
          : failed
            ? "border-signal-red/50"
            : running
              ? "border-signal-cyan/30"
              : ""
      }`}
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="label mb-0">Grading result</h2>
          <p className="font-mono text-2xs text-zinc-400">
            submission #{submission.id}
            {submission.ai_generated && (
              <span className="ml-2 inline-flex align-middle">
                <MentorMark>ai attempt</MentorMark>
              </span>
            )}
          </p>
        </div>
        <Verdict status={submission.status} score={submission.score} />
      </div>

      <GradingConsole submissionId={submission.id} />

      {running && (
        <div className="flex items-center gap-3 rounded-lg border border-signal-cyan/20 bg-signal-cyan/5 px-3 py-2.5">
          <Spinner
            label={
              submission.status === "queued"
                ? "queued for the emulator…"
                : "running on the emulator — live steps above"
            }
          />
        </div>
      )}

      {submission.evidence && (
        <p className="panel-inset mt-3 px-3 py-2 font-mono text-xs leading-relaxed text-zinc-300">
          <span className="text-phosphor-dim">$ </span>
          {submission.evidence}
        </p>
      )}

      {submission.checks.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="eyebrow">checks</span>
            <span className="font-mono text-2xs text-zinc-400">
              <span className={passCount === submission.checks.length ? "text-phosphor" : "text-zinc-200"}>
                {passCount}
              </span>
              /{submission.checks.length} passed
            </span>
          </div>
          <ul className="divide-y divide-ink-500/40 overflow-hidden rounded-lg border border-ink-500/60">
            {submission.checks.map((c, i) => (
              <li
                key={i}
                className={`flex items-start gap-3 px-3 py-2 text-sm ${
                  c.passed ? "bg-phosphor/[0.03]" : "bg-signal-red/[0.04]"
                }`}
              >
                <span
                  className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-sm font-mono text-2xs font-bold ${
                    c.passed ? "bg-phosphor text-ink-900" : "bg-signal-red text-ink-900"
                  }`}
                  aria-label={c.passed ? "passed" : "failed"}
                >
                  {c.passed ? "✓" : "✕"}
                </span>
                <span className="min-w-0 text-zinc-200">
                  {c.name}
                  {c.detail && <span className="text-zinc-400"> — {c.detail}</span>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {submission.evidence_bundle?.length > 0 && (
        <EvidenceBundle items={submission.evidence_bundle} />
      )}

      {submission.error && (
        <p className="mt-3 rounded-md border border-signal-amber/30 bg-signal-amber/5 px-3 py-2 font-mono text-xs text-signal-amber">
          {submission.error}
        </p>
      )}

      {passed && graderImplemented && <ReviewBlock taskId={taskId} />}
    </Panel>
  );
}

// The evidence bundle: the structured artifacts (baseline vs hooked logcat,
// frida trace, timeline) that show the technique actually took effect — not
// just that a flag string matched.
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
    <div className="mt-4 overflow-hidden rounded-lg border border-signal-cyan/30">
      <div className="flex items-center justify-between border-b border-signal-cyan/20 bg-signal-cyan/[0.06] px-3 py-1.5 font-mono text-2xs uppercase text-signal-cyan">
        <span>
          <span aria-hidden>▤ </span>evidence bundle · what the technique produced
        </span>
        <span className="text-signal-cyan/70">{items.length} artifacts</span>
      </div>
      <ul>
        {items.map((it, i) => {
          const isOpen = open === i;
          return (
            <li key={i} className="border-t border-ink-500/40 first:border-t-0">
              <button
                className={`flex w-full items-center gap-2 px-3 py-2 text-left font-mono text-xs transition-colors hover:bg-ink-700/60 ${
                  isOpen ? "text-phosphor" : "text-zinc-300"
                }`}
                onClick={() => setOpen(isOpen ? null : i)}
                aria-expanded={isOpen}
              >
                <span className="w-4 text-center text-signal-cyan" aria-hidden>
                  {icon[it.kind] ?? "•"}
                </span>
                <span className="flex-1 truncate">{it.label}</span>
                <span className="text-2xs uppercase text-zinc-400">{it.kind}</span>
                <span className="w-3 text-center text-zinc-400" aria-hidden>
                  {isOpen ? "−" : "+"}
                </span>
              </button>
              {isOpen && (
                <pre className="max-h-56 overflow-auto border-t border-ink-500/40 bg-ink-950 px-3 py-2 font-mono text-[10.5px] leading-relaxed text-zinc-300">
                  {it.content}
                </pre>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// Flat verdict badge: a glyph plus text, color-coded, no rotated stamp or glow.
function Verdict({ status, score }: { status: Submission["status"]; score: number }) {
  const base =
    "inline-flex items-center gap-2 rounded-md border px-3 py-1 font-mono text-sm font-semibold uppercase tracking-wide";
  if (status === "passed")
    return (
      <span className="flex items-center gap-3">
        <span className={`${base} border-phosphor/60 bg-phosphor/10 text-phosphor`} role="status">
          <span aria-hidden>✓</span>pass
        </span>
        <span className="font-mono text-sm text-zinc-300">
          <span className="text-xl font-bold text-phosphor">{score}</span> pts
        </span>
      </span>
    );
  if (status === "failed")
    return (
      <span className={`${base} border-signal-red/60 bg-signal-red/10 text-signal-red`} role="status">
        <span aria-hidden>✕</span>fail
      </span>
    );
  if (status === "error")
    return (
      <span className={`${base} border-signal-amber/60 bg-signal-amber/10 text-signal-amber`} role="status">
        <span aria-hidden>!</span>error
      </span>
    );
  return (
    <span className="chip border-signal-cyan/50 bg-signal-cyan/10 text-signal-cyan" role="status">
      <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-signal-cyan" />
      {status}
    </span>
  );
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
    <div className="mt-4 border-t border-ink-500/50 pt-4">
      {!review && (
        <button className="btn-ghost btn-sm border-signal-violet/40 text-signal-violet hover:border-signal-violet hover:bg-signal-violet/10 hover:text-signal-violet" onClick={getReview} disabled={busy}>
          <span aria-hidden>✦</span>
          {busy ? "mentor is thinking…" : "AI remediation review"}
        </button>
      )}
      {note && <p className="mt-2 font-mono text-xs text-signal-amber">{note}</p>}
      {review && (
        <div className="rounded-lg border border-signal-violet/25 bg-signal-violet/[0.04] p-4">
          <div className="mb-2">
            <MentorMark>remediation review</MentorMark>
          </div>
          <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-200">{review}</p>
        </div>
      )}
    </div>
  );
}
