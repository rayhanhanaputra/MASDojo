import { useEffect, useRef, useState } from "react";
import { API_BASE } from "../api/client";
import { api } from "../api/endpoints";

interface Line {
  ts: number;
  level: string; // info | check | done | error
  phase: string;
  msg: string;
}

// Live "flight recorder": streams the runner's grading steps over SSE into a
// phosphor terminal pane, so PASS/FAIL is the visible climax of a real pipeline
// (boot AVD → install APK → frida/mitmproxy → verdict) instead of a value that
// pops out of nowhere.
export function GradingConsole({ submissionId }: { submissionId: number }) {
  const [lines, setLines] = useState<Line[]>([]);
  const boxRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let es: EventSource | null = null;
    let cancelled = false;
    setLines([]);
    // Fetch a short-lived, stream-scoped token (don't put the account JWT in a URL).
    api
      .streamToken(submissionId)
      .then(({ token }) => {
        if (cancelled) return;
        es = new EventSource(
          `${API_BASE}/submissions/${submissionId}/stream?token=${encodeURIComponent(token)}`,
        );
        es.onmessage = (e) => {
          try {
            const line = JSON.parse(e.data) as Line;
            setLines((prev) => [...prev, line]);
            if (line.level === "done") es?.close();
          } catch {
            /* heartbeat / non-JSON line */
          }
        };
        es.onerror = () => es?.close();
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      es?.close();
    };
  }, [submissionId]);

  useEffect(() => {
    boxRef.current?.scrollTo(0, boxRef.current.scrollHeight);
  }, [lines]);

  if (lines.length === 0) return null;

  const finished = lines.some((l) => l.level === "done");
  const t0 = lines.find((l) => typeof l.ts === "number")?.ts ?? 0;
  const phase = [...lines].reverse().find((l) => l.phase)?.phase ?? "";

  return (
    <div className="console mb-4">
      {/* title bar */}
      <div className="relative z-10 flex items-center gap-3 border-b border-phosphor/20 bg-ink-900/90 px-3 py-1.5 font-mono text-2xs uppercase text-zinc-400">
        <span className="flex items-center gap-1.5" aria-hidden>
          <span className="h-2 w-2 rounded-full bg-ink-300" />
          <span className="h-2 w-2 rounded-full bg-ink-300" />
          <span className={`h-2 w-2 rounded-full ${finished ? "bg-phosphor-dim" : "bg-phosphor animate-blink"}`} />
        </span>
        <span className="text-zinc-200">flight recorder</span>
        <span className="text-zinc-600">·</span>
        <span>emulator pipeline</span>
        <span className="text-zinc-600">·</span>
        <span>#{submissionId}</span>
        <span className="ml-auto flex items-center gap-2">
          {phase && <span className="text-phosphor-dim">{phase}</span>}
          <span className={`chip ${finished ? "border-ink-400 text-zinc-400" : "border-phosphor/50 text-phosphor"}`}>
            {finished ? "rec end" : "● live"}
          </span>
        </span>
      </div>

      {!finished && <div aria-hidden className="console-sweep" />}

      <div
        ref={boxRef}
        className="console-text relative max-h-64 overflow-y-auto p-3 font-mono text-xs leading-[1.7]"
        role="log"
        aria-live="polite"
        aria-label="grading console"
      >
        {lines.map((l, i) => (
          <ConsoleLine key={i} line={l} t0={t0} />
        ))}
        {!finished && (
          <div className="text-phosphor" aria-hidden>
            <span className="mr-2 inline-block w-14 text-right text-zinc-600">&nbsp;</span>
            <span className="inline-block h-3 w-2 translate-y-0.5 bg-phosphor animate-blink" />
          </div>
        )}
      </div>
    </div>
  );
}

function Stamp({ ts, t0 }: { ts: number; t0: number }) {
  // Seconds since the first recorded line, e.g. "+03.21s". Falls back to a blank
  // column if the runner didn't attach timestamps.
  const dt = ts && t0 ? Math.max(0, ts - t0) : null;
  const text = dt === null ? "" : `+${dt.toFixed(2).padStart(5, "0")}s`;
  return (
    <span className="mr-2 inline-block w-14 select-none text-right text-zinc-600" aria-hidden>
      {text}
    </span>
  );
}

function ConsoleLine({ line, t0 }: { line: Line; t0: number }) {
  if (line.level === "done") {
    const pass = line.msg.toUpperCase().includes("PASSED");
    return (
      <div
        className={`mt-1 border-t pt-1 font-bold uppercase tracking-[0.2em] ${
          pass ? "border-phosphor/40 text-phosphor" : "border-signal-red/40 text-signal-red"
        }`}
        style={{ textShadow: pass ? "0 0 12px rgba(57,255,139,0.6)" : "0 0 12px rgba(255,92,92,0.5)" }}
      >
        <Stamp ts={line.ts} t0={t0} />■ {line.msg}
      </div>
    );
  }
  if (line.level === "error")
    return (
      <div className="text-signal-red">
        <Stamp ts={line.ts} t0={t0} />✗ {line.msg}
      </div>
    );
  if (line.level === "check") {
    const pass = line.msg.startsWith("PASS");
    return (
      <div className={pass ? "text-phosphor" : "text-signal-red"}>
        <Stamp ts={line.ts} t0={t0} />
        {pass ? "✓" : "✗"} {line.msg.replace(/^(PASS|FAIL)\s·\s/, "")}
      </div>
    );
  }
  return (
    <div className="text-zinc-300">
      <Stamp ts={line.ts} t0={t0} />
      <span className="text-phosphor-dim">▸</span> {line.msg}
    </div>
  );
}
