import type { ReactNode } from "react";
import type { NodeState, SubmissionStatus, SuccessType } from "../api/types";

/* ------------------------------------------------------------------ */
/* Brand                                                               */
/* ------------------------------------------------------------------ */

// The MASDojo wordmark: a phosphor "MAS" bracket + white "Dojo". `size` maps to
// a font size so the same mark works in the nav, the login hero and the boot screen.
export function Wordmark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const cls = size === "lg" ? "text-4xl" : size === "sm" ? "text-base" : "text-lg";
  return (
    <span className={`inline-flex items-baseline font-mono font-bold leading-none ${cls}`}>
      <span className="text-phosphor" style={{ textShadow: "0 0 18px rgba(57,255,139,0.45)" }}>
        MAS
      </span>
      <span className="text-zinc-100">Dojo</span>
      <span aria-hidden className="ml-0.5 inline-block h-[0.85em] w-[0.45em] translate-y-[0.1em] bg-phosphor/80 animate-blink" />
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Chips                                                               */
/* ------------------------------------------------------------------ */

export function MasvsBadge({ control }: { control: string }) {
  return (
    <span className="chip-masvs" title={`OWASP ${control}`}>
      {control}
    </span>
  );
}

// Every grader type has a fixed hue AND a fixed glyph, so it never relies on
// color alone. The same mapping is reused by the grader pipeline strip.
export const GRADER_META: Record<
  SuccessType,
  { label: string; glyph: string; chip: string; text: string; describe: string }
> = {
  flag: {
    label: "flag",
    glyph: "⚑",
    chip: "chip-flag",
    text: "text-signal-amber",
    describe: "flag match",
  },
  static_assert: {
    label: "static",
    glyph: "≡",
    chip: "chip-static",
    text: "text-zinc-200",
    describe: "static assert",
  },
  frida_assert: {
    label: "frida",
    glyph: "↯",
    chip: "chip-frida",
    text: "text-signal-rose",
    describe: "frida hook",
  },
  network_assert: {
    label: "network",
    glyph: "⇄",
    chip: "chip-network",
    text: "text-signal-cyan",
    describe: "mitmproxy capture",
  },
};

export function GraderBadge({ type }: { type: SuccessType }) {
  const m = GRADER_META[type];
  return (
    <span className={m.chip} title={`graded by ${m.describe}`}>
      <span aria-hidden>{m.glyph}</span>
      {m.label}
    </span>
  );
}

// The AI mentor's identity mark — violet ✦ everywhere the mentor speaks.
export function MentorMark({ children = "mentor" }: { children?: ReactNode }) {
  return (
    <span className="chip-mentor">
      <span aria-hidden>✦</span>
      {children}
    </span>
  );
}

const STATUS_META: Record<SubmissionStatus, { label: string; glyph: string; cls: string }> = {
  passed: { label: "pass", glyph: "✓", cls: "chip-pass" },
  failed: { label: "fail", glyph: "✕", cls: "chip-fail" },
  error: { label: "error", glyph: "!", cls: "chip border-signal-amber/50 bg-signal-amber/10 text-signal-amber" },
  running: { label: "running", glyph: "▶", cls: "chip border-signal-cyan/50 bg-signal-cyan/10 text-signal-cyan" },
  queued: { label: "queued", glyph: "…", cls: "chip border-ink-400 bg-ink-700/60 text-zinc-300" },
};

export function StatusChip({ status, score }: { status: SubmissionStatus; score?: number }) {
  const m = STATUS_META[status];
  return (
    <span className={m.cls}>
      <span aria-hidden>{m.glyph}</span>
      {m.label}
      {status === "passed" && typeof score === "number" && (
        <span className="ml-1 border-l border-phosphor/30 pl-1.5 normal-case tracking-normal">
          {score} pts
        </span>
      )}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Meters + state                                                      */
/* ------------------------------------------------------------------ */

// Difficulty as a 5-bar signal meter (ascending heights), with a text
// equivalent for screen readers. Fill colour ramps 1-2 dim, 3 amber, 4-5 red.
export function Difficulty({ level }: { level: number }) {
  const lvl = Math.max(0, Math.min(5, level));
  const fill = lvl >= 4 ? "bg-signal-red" : lvl === 3 ? "bg-signal-amber" : "bg-phosphor-dim";
  return (
    <span
      className="inline-flex items-end gap-[3px]"
      title={`difficulty ${lvl}/5`}
      role="img"
      aria-label={`difficulty ${lvl} of 5`}
    >
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`w-[3px] rounded-sm ${i < lvl ? fill : "bg-ink-400"}`}
          style={{ height: `${6 + i * 2}px` }}
        />
      ))}
    </span>
  );
}

const STATE_META: Record<NodeState, { symbol: string; cls: string; label: string }> = {
  locked: {
    symbol: "•",
    cls: "border-dashed border-ink-300 bg-ink-800 text-zinc-500",
    label: "prerequisites pending",
  },
  available: {
    symbol: "›",
    cls: "border-phosphor/60 bg-ink-800 text-phosphor",
    label: "available",
  },
  passed: {
    symbol: "✓",
    cls: "border-phosphor bg-phosphor text-ink-900 shadow-[0_0_12px_-2px_rgba(57,255,139,0.7)]",
    label: "cleared",
  },
};

export function StateDot({ state }: { state: NodeState }) {
  const m = STATE_META[state];
  return (
    <span
      className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border font-mono text-xs font-bold leading-none ${m.cls}`}
      role="img"
      aria-label={m.label}
      title={m.label}
    >
      {m.symbol}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Layout                                                              */
/* ------------------------------------------------------------------ */

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`panel p-5 ${className}`}>{children}</section>;
}

export function PageHeader({
  title,
  subtitle,
  aside,
  eyebrow,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  aside?: ReactNode;
  eyebrow?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && <div className="eyebrow mb-2">{eyebrow}</div>}
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-50 sm:text-[1.75rem]">
          {title}
        </h1>
        {subtitle && <p className="mt-1.5 max-w-2xl text-sm text-zinc-400">{subtitle}</p>}
      </div>
      {aside}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Feedback                                                            */
/* ------------------------------------------------------------------ */

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 font-mono text-sm text-phosphor-dim" role="status">
      <span className="relative grid h-3.5 w-3.5 place-items-center">
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-phosphor/20 border-t-phosphor" />
      </span>
      {label}
    </span>
  );
}

export function ErrorText({ children }: { children: ReactNode }) {
  return (
    <p className="flex items-start gap-2 rounded-md border border-signal-red/30 bg-signal-red/5 px-3 py-2 font-mono text-xs text-signal-red" role="alert">
      <span aria-hidden>✕</span>
      <span>{children}</span>
    </p>
  );
}

// Shimmering placeholder block. Compose several to sketch a page's shape while
// it loads, so the layout doesn't jump when the data lands.
export function Skeleton({ className = "" }: { className?: string }) {
  return <span aria-hidden className={`skeleton block ${className}`} />;
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-ink-500/50 px-4 py-3">
      <Skeleton className="h-6 w-6 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-3.5 w-1/2" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="h-3 w-10" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Grader pipeline strip                                               */
/* ------------------------------------------------------------------ */

// A stage-by-stage picture of what the emulator runner does for this task.
// The stage that is currently live lights up while a submission is in flight,
// and the last stage becomes the verdict. This is what makes a screenshot say
// "graded by a real device pipeline" without reading any text.
export function GraderPipeline({
  type,
  status,
}: {
  type: SuccessType;
  status?: SubmissionStatus | null;
}) {
  const m = GRADER_META[type];
  const stages = [
    { key: "queue", label: "queue", glyph: "≣" },
    { key: "boot", label: "boot AVD", glyph: "▣" },
    { key: "install", label: "install APK", glyph: "⇩" },
    { key: "probe", label: m.describe, glyph: m.glyph },
    { key: "verdict", label: "signed verdict", glyph: "✦" },
  ];

  // Which stage index is "live" for the current status.
  const live =
    status === "queued" ? 0 : status === "running" ? 3 : status ? 4 : -1;
  const terminal = status === "passed" || status === "failed" || status === "error";

  return (
    <ol
      className="flex flex-wrap items-center gap-y-2 font-mono text-2xs uppercase"
      aria-label="grading pipeline"
    >
      {stages.map((s, i) => {
        const done = terminal ? i <= 4 : live > i;
        const active = !terminal && live === i;
        const isVerdict = i === 4;
        const verdictCls =
          status === "passed"
            ? "border-phosphor bg-phosphor/15 text-phosphor"
            : status === "failed"
              ? "border-signal-red bg-signal-red/10 text-signal-red"
              : status === "error"
                ? "border-signal-amber bg-signal-amber/10 text-signal-amber"
                : "";
        const cls =
          isVerdict && terminal
            ? verdictCls
            : active
              ? "border-phosphor/70 bg-phosphor/10 text-phosphor animate-pulse-ring"
              : done
                ? "border-phosphor/40 bg-ink-800 text-phosphor-dim"
                : "border-ink-400 bg-ink-800/60 text-zinc-500";
        return (
          <li key={s.key} className="flex items-center">
            <span
              className={`inline-flex h-6 items-center gap-1.5 rounded border px-2 transition-colors ${cls}`}
              aria-current={active ? "step" : undefined}
            >
              <span aria-hidden className={i === 3 ? m.text : undefined}>
                {s.glyph}
              </span>
              {s.label}
            </span>
            {i < stages.length - 1 && (
              <span
                aria-hidden
                className={`mx-1 h-px w-4 sm:w-6 ${done || active ? "bg-phosphor/50" : "bg-ink-400"}`}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}
