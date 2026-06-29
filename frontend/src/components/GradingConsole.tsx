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

  return (
    <div className="mb-3 overflow-hidden rounded-md border border-ink-500/70">
      <div className="flex items-center gap-2 border-b border-ink-500/60 bg-ink-800 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-zinc-500">
        <span className="h-2 w-2 animate-pulse rounded-full bg-phosphor" />
        grading console · emulator pipeline
      </div>
      <div
        ref={boxRef}
        className="max-h-56 overflow-y-auto bg-ink-900/90 p-3 font-mono text-[11px] leading-relaxed"
      >
        {lines.map((l, i) => (
          <ConsoleLine key={i} line={l} />
        ))}
      </div>
    </div>
  );
}

function ConsoleLine({ line }: { line: Line }) {
  if (line.level === "done") {
    const pass = line.msg.toUpperCase().includes("PASSED");
    return (
      <div className={`font-bold ${pass ? "text-phosphor" : "text-signal-red"}`}>
        ── {line.msg} ──
      </div>
    );
  }
  if (line.level === "error") return <div className="text-signal-red">✗ {line.msg}</div>;
  if (line.level === "check") {
    const pass = line.msg.startsWith("PASS");
    return (
      <div className={pass ? "text-phosphor" : "text-signal-red"}>
        {pass ? "✓" : "✗"} {line.msg.replace(/^(PASS|FAIL)\s·\s/, "")}
      </div>
    );
  }
  return (
    <div className="text-zinc-400">
      <span className="text-phosphor-dim">▸</span> {line.msg}
    </div>
  );
}
