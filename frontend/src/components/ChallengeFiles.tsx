import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";
import { Panel } from "./ui";

interface FileEntry {
  path: string;
  size: number;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Challenge files: the committed artifacts a learner analyses to solve a task
// (decoded resources, prefs/log/backup dumps, encrypted blobs, captured
// traffic). This is what closes the loop — the technique is applied against
// these, and the grader checks the value they yield.
export function ChallengeFiles({ taskId }: { taskId: string }) {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);

  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setFiles([]);
    setOpen(null);
    setLoaded(false);
    api
      .listArtifacts(taskId)
      .then(setFiles)
      .catch(() => setFiles([]))
      .finally(() => setLoaded(true));
  }, [taskId]);

  // No per-task files: this task is worked against the shared practice target,
  // so point the learner at where they fetch it instead of showing an empty gap.
  if (loaded && files.length === 0) {
    return (
      <Panel>
        <h2 className="label">Get the target</h2>
        <p className="text-sm leading-relaxed text-zinc-400">
          This task has no per-task files — you work it against the practice target,{" "}
          <span className="font-mono text-zinc-200">MASDojo.apk</span>. Download and install it,
          analyse it with your own tools, then submit what you recover below.
        </p>
        <ol className="mt-3 space-y-1.5 font-mono text-xs text-zinc-400">
          <li>
            <span className="text-phosphor-dim">1. </span>
            Grab <span className="text-zinc-200">MASDojo.apk</span> from the{" "}
            <Link to="/" className="rounded text-phosphor hover:underline">
              skill map
            </Link>{" "}
            (if it isn&apos;t built yet, run <span className="text-zinc-200">make apps</span>).
          </li>
          <li>
            <span className="text-phosphor-dim">2. </span>
            <span className="text-zinc-200">adb install -r MASDojo.apk</span>, then analyse it.
          </li>
          <li>
            <span className="text-phosphor-dim">3. </span>
            Submit your result to the emulator grader below.
          </li>
        </ol>
      </Panel>
    );
  }

  if (files.length === 0) return null;

  async function view(path: string) {
    setOpen(path);
    setContent("loading…");
    setBusy(true);
    try {
      setContent(await api.getArtifactText(taskId, path));
    } catch {
      setContent("(failed to load)");
    } finally {
      setBusy(false);
    }
  }

  async function download(path: string) {
    try {
      const text = await api.getArtifactText(taskId, path);
      const url = URL.createObjectURL(new Blob([text]));
      const a = document.createElement("a");
      a.href = url;
      a.download = path.split("/").pop() || "artifact";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    }
  }

  return (
    <Panel>
      <div className="mb-1 flex items-center justify-between">
        <h2 className="label mb-0">Challenge files</h2>
        <span className="font-mono text-2xs uppercase text-zinc-500">{files.length} artifacts</span>
      </div>
      <p className="mb-3 text-xs leading-relaxed text-zinc-400">
        The artifacts to analyse for this task. Apply the technique to these, then submit what you
        recover.
      </p>
      <ul className="divide-y divide-ink-500/40 overflow-hidden rounded-lg border border-ink-500/60">
        {files.map((f) => {
          const isOpen = open === f.path;
          return (
            <li
              key={f.path}
              className={`flex items-center justify-between gap-2 px-3 py-2 transition-colors ${
                isOpen ? "bg-phosphor/[0.05]" : "hover:bg-ink-700/60"
              }`}
            >
              <button
                className={`flex min-w-0 items-center gap-2 text-left font-mono text-xs ${
                  isOpen ? "text-phosphor" : "text-zinc-200 hover:text-phosphor"
                }`}
                onClick={() => view(f.path)}
                title={f.path}
                aria-expanded={isOpen}
              >
                <span aria-hidden className={isOpen ? "text-phosphor" : "text-zinc-500"}>
                  {isOpen ? "▾" : "▸"}
                </span>
                <span className="truncate">{f.path}</span>
              </button>
              <div className="flex shrink-0 items-center gap-3">
                <span className="font-mono text-2xs text-zinc-500">{formatSize(f.size)}</span>
                <button
                  className="rounded font-mono text-2xs uppercase text-zinc-400 transition-colors hover:text-signal-cyan"
                  onClick={() => download(f.path)}
                >
                  ⇩ download
                </button>
              </div>
            </li>
          );
        })}
      </ul>

      {open && (
        <div className="mt-3 overflow-hidden rounded-lg border border-ink-500/60 animate-rise">
          <div className="flex items-center justify-between border-b border-ink-500/60 bg-ink-800 px-3 py-1.5">
            <span className="truncate font-mono text-xs text-zinc-300">{open}</span>
            <button
              className="rounded font-mono text-2xs uppercase text-zinc-400 hover:text-signal-red"
              onClick={() => setOpen(null)}
            >
              close ✕
            </button>
          </div>
          <pre className="max-h-72 overflow-auto bg-ink-950 p-3 font-mono text-xs leading-relaxed text-zinc-200">
            {busy ? "loading…" : content}
          </pre>
        </div>
      )}
    </Panel>
  );
}
