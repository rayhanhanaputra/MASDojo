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
    <div className="panel flex items-center justify-between gap-4 border-signal-amber/40 p-5">
      <div>
        <p className="font-mono text-[11px] uppercase tracking-widest text-signal-amber">
          practice target
        </p>
        <p className="mt-1 text-lg font-semibold text-zinc-100">MASDojo.apk</p>
        <p className="mt-1 text-sm text-zinc-500">
          One deliberately-vulnerable banking app bundling every technique in the syllabus.
          Install on the emulator: <code className="font-mono text-zinc-400">adb install -r MASDojo.apk</code>
        </p>
      </div>
      <a
        className="btn-primary shrink-0"
        href={`${API_BASE}/download/target-apk`}
        download="MASDojo.apk"
      >
        Download ({mb} MB)
      </a>
    </div>
  );
}
