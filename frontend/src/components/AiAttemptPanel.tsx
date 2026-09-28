import { useEffect, useRef, useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Submission } from "../api/types";
import { Spinner } from "./ui";

const TERMINAL = new Set(["passed", "failed", "error"]);

// AI-as-adversary: let the AI propose a solution, then let the real grader judge
// it. On seeded / device-dependent tasks the model can't know the answer, so it
// usually FAILS — the point being that an unverified AI answer is not a
// solution. The grader, running on the real target, is the source of truth.
export function AiAttemptPanel({ taskId }: { taskId: string }) {
  const [candidate, setCandidate] = useState("");
  const [field, setField] = useState("value");
  const [note, setNote] = useState("");
  const [sub, setSub] = useState<Submission | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const poll = useRef<number | null>(null);

  useEffect(() => () => { if (poll.current) window.clearInterval(poll.current); }, []);

  async function run() {
    setBusy(true);
    setErr("");
    setSub(null);
    setCandidate("");
    try {
      const a = await api.mentorAttempt(taskId);
      setCandidate(a.candidate);
      setField(a.field);
      setNote(a.note);
      if (poll.current) window.clearInterval(poll.current);
      poll.current = window.setInterval(async () => {
        try {
          const s = await api.getSubmission(a.submission_id);
          setSub(s);
          if (TERMINAL.has(s.status)) {
            window.clearInterval(poll.current!);
            poll.current = null;
            setBusy(false);
          }
        } catch {
          window.clearInterval(poll.current!);
          poll.current = null;
          setBusy(false);
        }
      }, 1500);
    } catch (e) {
      setBusy(false);
      if (e instanceof ApiError && e.status === 409) {
        setErr("Add your AI key in Settings to let the AI attempt this task.");
      } else {
        setErr(e instanceof Error ? e.message : "AI attempt failed");
      }
    }
  }

  const verdict = sub && TERMINAL.has(sub.status) ? sub.status : null;

  return (
    <div className="mt-4 border-t border-ink-500/50 pt-4">
      <button
        className="btn-ghost btn-sm w-full border-signal-violet/40 text-signal-violet hover:border-signal-violet hover:bg-signal-violet/10 hover:text-signal-violet"
        onClick={run}
        disabled={busy}
      >
        <span aria-hidden>✦</span>
        {busy ? "AI attempting…" : "Let the AI try — the grader judges"}
      </button>
      {err && <p className="mt-2 font-mono text-xs text-signal-amber">{err}</p>}

      {candidate && (
        <div className="mt-3 space-y-3 animate-rise">
          {/* two-column face-off: the model's claim vs the emulator's ruling */}
          <div className="overflow-hidden rounded-lg border border-ink-500/60">
            <div className="flex items-center justify-between border-b border-ink-500/60 bg-signal-violet/[0.06] px-3 py-1.5 font-mono text-2xs uppercase">
              <span className="text-signal-violet">
                <span aria-hidden>✦ </span>AI proposed
              </span>
              <span className="text-zinc-500">{field}</span>
            </div>
            <pre className="max-h-32 overflow-auto bg-ink-950 px-3 py-2 font-mono text-xs text-zinc-200">
              {candidate}
            </pre>
            <div
              className={`flex items-center justify-between gap-2 border-t px-3 py-2 ${
                verdict === "passed"
                  ? "border-phosphor/40 bg-phosphor/[0.06]"
                  : verdict === "failed"
                    ? "border-signal-red/40 bg-signal-red/[0.06]"
                    : verdict === "error"
                      ? "border-signal-amber/40 bg-signal-amber/[0.06]"
                      : "border-ink-500/60 bg-ink-800"
              }`}
            >
              <span className="font-mono text-2xs uppercase text-zinc-400">
                <span aria-hidden className="text-phosphor-dim">▣ </span>emulator verdict
              </span>
              {!verdict && <Spinner label="grading…" />}
              {verdict === "passed" && (
                <span className="font-mono text-xs font-bold text-phosphor">
                  ✓ AI was right — verified
                </span>
              )}
              {verdict === "failed" && (
                <span className="font-mono text-xs font-bold text-signal-red">
                  ✕ AI was wrong — don't trust it unverified
                </span>
              )}
              {verdict === "error" && (
                <span className="font-mono text-xs font-bold text-signal-amber">! grader error</span>
              )}
            </div>
          </div>

          {verdict && sub?.evidence && (
            <p className="panel-inset px-3 py-2 font-mono text-xs leading-relaxed text-zinc-300">
              <span className="text-phosphor-dim">$ </span>
              {sub.evidence}
            </p>
          )}
          <p className="text-[11px] leading-relaxed text-zinc-400">{note}</p>
        </div>
      )}
    </div>
  );
}
