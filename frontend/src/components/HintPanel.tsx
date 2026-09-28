import { useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { HintResponse, TaskDetail } from "../api/types";
import { MentorMark, Panel } from "./ui";

interface RevealedHint extends HintResponse {
  key: string;
}

// The hint panel mixes the task's canned tiered hints with the BYOK AI mentor
// (adaptive hints + explain-this). Both record hint usage, lowering the score.
export function HintPanel({ task }: { task: TaskDetail; passed: boolean }) {
  const [hints, setHints] = useState<RevealedHint[]>([]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState("");
  const [snippet, setSnippet] = useState("");
  const [explanation, setExplanation] = useState("");

  function add(h: HintResponse, source: string) {
    setHints((prev) => [...prev, { ...h, key: `${source}-${h.tier}-${prev.length}` }]);
  }

  async function reveal(tier: number) {
    setNote("");
    setBusy(true);
    try {
      add(await api.revealHint(task.id, tier), "static");
    } catch (e) {
      setNote(e instanceof ApiError ? e.message : "Could not reveal hint");
    } finally {
      setBusy(false);
    }
  }

  async function aiHint() {
    setNote("");
    setBusy(true);
    try {
      // Pass the learner's own attempt/scratch so the mentor hint is adaptive.
      add(await api.mentorHint(task.id, attempt, ""), "ai");
    } catch (e) {
      setNote(
        e instanceof ApiError && e.status === 409
          ? "Add your AI key in Settings to use the adaptive mentor."
          : e instanceof Error
            ? e.message
            : "Mentor unavailable",
      );
    } finally {
      setBusy(false);
    }
  }

  async function explain() {
    if (!snippet.trim()) return;
    setNote("");
    setBusy(true);
    setExplanation("");
    try {
      const r = await api.mentorExplain(task.id, snippet);
      setExplanation(r.explanation);
    } catch (e) {
      setNote(
        e instanceof ApiError && e.status === 409
          ? "Add your AI key in Settings to use explain-this."
          : e instanceof Error
            ? e.message
            : "Mentor unavailable",
      );
    } finally {
      setBusy(false);
    }
  }

  const tiers = [1, 2, 3].slice(0, task.hint_count);
  const revealedTiers = new Set(hints.filter((h) => h.source === "static").map((h) => h.tier));

  return (
    <Panel className="sticky top-20 space-y-4">
      <div>
        <div className="flex items-center justify-between">
          <h2 className="label mb-0">Hints</h2>
          <span className="font-mono text-2xs uppercase text-zinc-500">
            {hints.length} used
          </span>
        </div>
        <p className="mt-1.5 text-xs leading-relaxed text-zinc-400">
          Each hint you open lowers your score. The full solution stays locked until tier 3 or a
          few attempts.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {tiers.map((t) => {
          const seen = revealedTiers.has(t);
          return (
            <button
              key={t}
              className={`btn-ghost btn-sm ${seen ? "border-phosphor/40 text-phosphor" : ""}`}
              onClick={() => reveal(t)}
              disabled={busy}
              aria-pressed={seen}
            >
              {seen && <span aria-hidden>✓</span>}
              Hint {t}
            </button>
          );
        })}
        <button
          className="btn-ghost btn-sm border-signal-amber/40 text-signal-amber hover:border-signal-amber hover:bg-signal-amber/10 hover:text-signal-amber"
          onClick={() => reveal(4)}
          disabled={busy}
        >
          Solution
        </button>
        <button
          className="btn-ghost btn-sm border-signal-violet/40 text-signal-violet hover:border-signal-violet hover:bg-signal-violet/10 hover:text-signal-violet"
          onClick={aiHint}
          disabled={busy}
        >
          <span aria-hidden>✦</span>
          AI hint
        </button>
      </div>

      <textarea
        className="input min-h-[56px] font-mono text-xs"
        placeholder="optional: what have you tried? (makes the ✦ AI hint adaptive to your attempt)"
        value={attempt}
        spellCheck={false}
        maxLength={8000}
        onChange={(e) => setAttempt(e.target.value)}
        aria-label="what have you tried"
      />

      {note && <p className="font-mono text-xs text-signal-amber">{note}</p>}

      <div className="space-y-3">
        {hints.map((h) => {
          const ai = h.source === "ai";
          return (
            <div
              key={h.key}
              className={`animate-rise rounded-lg border px-3 py-2.5 ${
                h.is_solution
                  ? "border-signal-amber/40 bg-signal-amber/5"
                  : ai
                    ? "border-signal-violet/30 bg-signal-violet/[0.04]"
                    : "border-ink-400 bg-ink-900/50"
              }`}
            >
              <div className="mb-1.5 flex items-center gap-2">
                {ai ? (
                  <MentorMark>mentor · tier {h.tier}</MentorMark>
                ) : (
                  <span className="chip-masvs">
                    hint · tier {h.tier}
                  </span>
                )}
                {h.is_solution && <span className="chip-flag">solution</span>}
              </div>
              <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-200">{h.content}</p>
            </div>
          );
        })}
      </div>

      <div className="border-t border-ink-500/50 pt-4">
        <div className="flex items-center justify-between">
          <h3 className="label mb-0">Explain this</h3>
          <MentorMark />
        </div>
        <p className="mb-2 mt-1.5 text-xs leading-relaxed text-zinc-400">
          Paste decompiled smali/Kotlin or a Frida error — the mentor explains it without solving
          the task.
        </p>
        <textarea
          className="input min-h-[80px] font-mono text-xs"
          placeholder="paste a snippet…"
          value={snippet}
          spellCheck={false}
          maxLength={12000}
          onChange={(e) => setSnippet(e.target.value)}
          aria-label="snippet to explain"
        />
        <button className="btn-ghost btn-sm mt-2 w-full" onClick={explain} disabled={busy || !snippet.trim()}>
          <span aria-hidden className="text-signal-violet">✦</span>
          Explain
        </button>
        {explanation && (
          <div className="animate-rise mt-2 rounded-lg border border-signal-violet/30 bg-signal-violet/[0.04] px-3 py-2.5">
            <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-200">{explanation}</p>
          </div>
        )}
      </div>
    </Panel>
  );
}
