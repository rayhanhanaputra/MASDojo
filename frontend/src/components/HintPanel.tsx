import { useState } from "react";
import { api } from "../api/endpoints";
import { ApiError } from "../api/client";
import type { HintResponse, TaskDetail } from "../api/types";
import { Panel } from "./ui";

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

  return (
    <Panel className="sticky top-20 space-y-4">
      <div>
        <h2 className="label">Hints</h2>
        <p className="text-xs text-zinc-500">
          Each hint you open lowers your score. The full solution stays locked until tier 3 or a
          few attempts.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {tiers.map((t) => (
          <button key={t} className="btn-ghost text-xs" onClick={() => reveal(t)} disabled={busy}>
            Hint {t}
          </button>
        ))}
        <button className="btn-ghost text-xs" onClick={() => reveal(4)} disabled={busy}>
          Solution
        </button>
        <button className="btn-ghost text-xs text-phosphor" onClick={aiHint} disabled={busy}>
          ✦ AI hint
        </button>
      </div>

      <textarea
        className="input min-h-[56px] font-mono text-xs"
        placeholder="optional: what have you tried? (makes the ✦ AI hint adaptive to your attempt)"
        value={attempt}
        spellCheck={false}
        onChange={(e) => setAttempt(e.target.value)}
      />

      {note && <p className="font-mono text-xs text-signal-amber">{note}</p>}

      <div className="space-y-3">
        {hints.map((h) => (
          <div
            key={h.key}
            className={`rounded-md border px-3 py-2 ${
              h.is_solution ? "border-signal-amber/40 bg-signal-amber/5" : "border-ink-500 bg-ink-900/50"
            }`}
          >
            <div className="mb-1 flex items-center gap-2 font-mono text-[10px] uppercase tracking-wide">
              <span className={h.source === "ai" ? "text-phosphor" : "text-zinc-500"}>
                {h.source === "ai" ? "mentor" : "hint"} · tier {h.tier}
                {h.is_solution ? " · solution" : ""}
              </span>
            </div>
            <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">{h.content}</p>
          </div>
        ))}
      </div>

      <div className="border-t border-ink-500/50 pt-4">
        <h3 className="label">Explain this</h3>
        <p className="mb-2 text-xs text-zinc-600">
          Paste decompiled smali/Kotlin or a Frida error — the mentor explains it without solving
          the task.
        </p>
        <textarea
          className="input min-h-[80px] font-mono text-xs"
          placeholder="paste a snippet…"
          value={snippet}
          spellCheck={false}
          onChange={(e) => setSnippet(e.target.value)}
        />
        <button className="btn-ghost mt-2 w-full text-xs" onClick={explain} disabled={busy}>
          ✦ Explain
        </button>
        {explanation && (
          <p className="mt-2 whitespace-pre-line rounded-md bg-ink-900/50 px-3 py-2 text-sm leading-relaxed text-zinc-300">
            {explanation}
          </p>
        )}
      </div>
    </Panel>
  );
}
