import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import { API_BASE } from "../api/client";

type Status = { available: boolean; size: number };

// The all-in-one vulnerable target: one APK (MASDojo.apk) that bundles every
// technique in the curriculum, à la Damn Vulnerable Bank. Install it on the
// emulator and practise the whole syllabus against a single target. When the
// APK hasn't been built yet the card stays visible and explains how to build
// it, so a learner is never left staring at a missing download.
export function TargetAppCard() {
  const [status, setStatus] = useState<Status | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .targetApkStatus()
      .then((s) => alive && setStatus(s))
      .catch(() => alive && setStatus({ available: false, size: 0 }))
      .finally(() => alive && setLoaded(true));
    return () => {
      alive = false;
    };
  }, []);

  // Hold layout until the status call settles, then always render the card.
  if (!loaded) return null;

  const available = status?.available ?? false;
  const mb = status ? (status.size / (1024 * 1024)).toFixed(1) : "0.0";

  return (
    <div
      className={`panel flex flex-wrap items-center justify-between gap-4 p-5 ${
        available ? "border-signal-amber/40" : "border-ink-500/70"
      }`}
    >
      <div className="flex min-w-0 items-start gap-4">
        <span
          aria-hidden
          className={`grid h-11 w-11 shrink-0 place-items-center rounded-lg border font-mono text-lg ${
            available
              ? "border-signal-amber/40 bg-signal-amber/10 text-signal-amber"
              : "border-ink-400 bg-ink-800 text-zinc-500"
          }`}
        >
          ▣
        </span>
        <div className="min-w-0">
          <p className={`font-mono text-2xs uppercase ${available ? "text-signal-amber" : "text-zinc-500"}`}>
            practice target
          </p>
          <p className="mt-0.5 text-lg font-semibold tracking-tight text-zinc-50">MASDojo.apk</p>
          {available ? (
            <>
              <p className="mt-1 text-sm text-zinc-400">
                One deliberately-vulnerable banking app bundling every technique in the syllabus.
              </p>
              <code className="mt-2 inline-block rounded border border-ink-500/70 bg-ink-950 px-2 py-1 font-mono text-xs text-zinc-300">
                <span className="text-phosphor-dim">$ </span>adb install -r MASDojo.apk
              </code>
            </>
          ) : (
            <>
              <p className="mt-1 text-sm text-zinc-400">
                The practice target hasn&apos;t been built yet. Build it once, then this download
                unlocks.
              </p>
              <code className="mt-2 inline-block rounded border border-ink-500/70 bg-ink-950 px-2 py-1 font-mono text-xs text-zinc-300">
                <span className="text-phosphor-dim">$ </span>make apps
              </code>
            </>
          )}
        </div>
      </div>
      {available ? (
        <a
          className="btn-ghost shrink-0 border-signal-amber/50 text-signal-amber hover:border-signal-amber hover:bg-signal-amber/10 hover:text-signal-amber"
          href={`${API_BASE}/download/target-apk`}
          download="MASDojo.apk"
        >
          <span aria-hidden>⇩</span>
          Download · {mb} MB
        </a>
      ) : (
        <button
          className="btn-ghost shrink-0"
          disabled
          aria-disabled="true"
          title="Run `make apps` to build MASDojo.apk"
        >
          <span aria-hidden>⇩</span>
          Not built yet
        </button>
      )}
    </div>
  );
}
