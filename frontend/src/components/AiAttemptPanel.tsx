import { useEffect, useRef, useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { Submission } from "../api/types";

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
    <div className="mt-4 border-t border-ink-500/50 pt-3">
      <button className="btn-ghost text-xs" onClick={run} disabled={busy}>
        {busy ? "AI attempting…" : "✦ Let the AI try (the grader judges)"}
      </button>
      {err && <p className="mt-2 font-mono text-xs text-signal-amber">{err}</p>}

      {candidate && (
        <div className="mt-3 space-y-2">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-600">
              AI proposed ({field})
            </p>
            <pre className="mt-1 max-h-32 overflow-auto rounded-md bg-ink-900/80 px-3 py-2 font-mono text-[11px] text-zinc-300">
              {candidate}
            </pre>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-widest text-zinc-600">
              grader verdict
            </span>
            {!verdict && <span className="font-mono text-xs text-signal-cyan">grading…</span>}
            {verdict === "passed" && (
              <span className="font-mono text-xs font-bold text-phosphor">
                AI was right ✓ (verified)
              </span>
            )}
            {verdict === "failed" && (
              <span className="font-mono text-xs font-bold text-signal-red">
                AI was wrong ✕ — don't trust it unverified
              </span>
            )}
            {verdict === "error" && (
              <span className="font-mono text-xs font-bold text-signal-amber">grader error</span>
            )}
          </div>

          {verdict && sub?.evidence && (
            <p className="rounded-md bg-ink-900/70 px-3 py-2 font-mono text-[11px] text-zinc-400">
              {sub.evidence}
            </p>
          )}
          <p className="text-[11px] leading-relaxed text-zinc-500">{note}</p>
        </div>
      )}
    </div>
  );
}
