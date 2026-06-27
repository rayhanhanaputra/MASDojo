import type { ReactNode } from "react";
import type { NodeState, SuccessType } from "../api/types";

export function MasvsBadge({ control }: { control: string }) {
  return (
    <span className="rounded border border-signal-cyan/40 bg-signal-cyan/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-signal-cyan">
      {control}
    </span>
  );
}

const GRADER_LABEL: Record<SuccessType, string> = {
  flag: "flag",
  static_assert: "static",
  frida_assert: "frida",
  network_assert: "network",
};

export function GraderBadge({ type }: { type: SuccessType }) {
  return (
    <span className="rounded border border-ink-500 bg-ink-700 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-zinc-400">
      {GRADER_LABEL[type]}
    </span>
  );
}

export function Difficulty({ level }: { level: number }) {
  return (
    <span className="inline-flex items-center gap-0.5" title={`difficulty ${level}/5`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`h-1.5 w-1.5 rounded-full ${
            i < level ? "bg-signal-amber" : "bg-ink-500"
          }`}
        />
      ))}
    </span>
  );
}

const STATE_STYLE: Record<NodeState, string> = {
  locked: "border-ink-500 text-zinc-600",
  available: "border-phosphor/40 text-phosphor",
  passed: "border-phosphor bg-phosphor/10 text-phosphor",
};

export function StateDot({ state }: { state: NodeState }) {
  const symbol = state === "passed" ? "✓" : state === "available" ? "›" : "✕";
  return (
    <span
      className={`grid h-5 w-5 place-items-center rounded-full border font-mono text-[11px] ${STATE_STYLE[state]}`}
    >
      {symbol}
    </span>
  );
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`panel p-5 ${className}`}>{children}</section>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 font-mono text-sm text-phosphor-dim">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-phosphor/30 border-t-phosphor" />
      {label}
    </span>
  );
}

export function ErrorText({ children }: { children: ReactNode }) {
  return <p className="font-mono text-sm text-signal-red">{children}</p>;
}
