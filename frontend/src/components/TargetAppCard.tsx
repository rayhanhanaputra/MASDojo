import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import { API_BASE } from "../api/client";

// The all-in-one vulnerable target: one APK (MASDojo.apk) that bundles every
// technique in the curriculum, à la Damn Vulnerable Bank. Install it on the
// emulator and practise the whole syllabus against a single target. The card
// hides itself until the APK has actually been built.
export function TargetAppCard() {
  const [status, setStatus] = useState<{ available: boolean; size: number } | null>(null);

  useEffect(() => {
    api.targetApkStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  if (!status?.available) return null;

  const mb = (status.size / (1024 * 1024)).toFixed(1);

  return (
    <div className="panel flex flex-wrap items-center justify-between gap-4 border-signal-amber/40 p-5">
      <div className="flex min-w-0 items-start gap-4">
        <span
          aria-hidden
          className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-signal-amber/40 bg-signal-amber/10 font-mono text-lg text-signal-amber"
        >
          ▣
        </span>
        <div className="min-w-0">
          <p className="font-mono text-2xs uppercase text-signal-amber">practice target</p>
          <p className="mt-0.5 text-lg font-semibold tracking-tight text-zinc-50">MASDojo.apk</p>
          <p className="mt-1 text-sm text-zinc-400">
            One deliberately-vulnerable banking app bundling every technique in the syllabus.
          </p>
          <code className="mt-2 inline-block rounded border border-ink-500/70 bg-ink-950 px-2 py-1 font-mono text-xs text-zinc-300">
            <span className="text-phosphor-dim">$ </span>adb install -r MASDojo.apk
          </code>
        </div>
      </div>
      <a
        className="btn-ghost shrink-0 border-signal-amber/50 text-signal-amber hover:border-signal-amber hover:bg-signal-amber/10 hover:text-signal-amber"
        href={`${API_BASE}/download/target-apk`}
        download="MASDojo.apk"
      >
        <span aria-hidden>⇩</span>
        Download · {mb} MB
      </a>
    </div>
  );
}
