import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import { Panel } from "./ui";

interface FileEntry {
  path: string;
  size: number;
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

  useEffect(() => {
    setFiles([]);
    setOpen(null);
    api.listArtifacts(taskId).then(setFiles).catch(() => setFiles([]));
  }, [taskId]);

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
      <h2 className="label">Challenge files</h2>
      <p className="mb-3 text-xs text-zinc-500">
        The artifacts to analyse for this task. Apply the technique to these, then submit what you
        recover.
      </p>
      <ul className="divide-y divide-ink-500/40 rounded-md border border-ink-500/60">
        {files.map((f) => (
          <li key={f.path} className="flex items-center justify-between gap-2 px-3 py-2">
            <button
              className={`truncate text-left font-mono text-xs ${
                open === f.path ? "text-phosphor" : "text-zinc-300 hover:text-phosphor"
              }`}
              onClick={() => view(f.path)}
              title={f.path}
            >
              <span className="text-phosphor-dim">📄</span> {f.path}
            </button>
            <div className="flex shrink-0 items-center gap-3">
              <span className="font-mono text-[10px] text-zinc-600">{f.size} B</span>
              <button
                className="font-mono text-[10px] text-zinc-500 hover:text-signal-cyan"
                onClick={() => download(f.path)}
              >
                download
              </button>
            </div>
          </li>
        ))}
      </ul>

      {open && (
        <div className="mt-3 overflow-hidden rounded-md border border-ink-500/60">
          <div className="flex items-center justify-between border-b border-ink-500/60 bg-ink-800 px-3 py-1.5">
            <span className="truncate font-mono text-[11px] text-zinc-400">{open}</span>
            <button
              className="font-mono text-[10px] text-zinc-500 hover:text-signal-red"
              onClick={() => setOpen(null)}
            >
              close
            </button>
          </div>
          <pre className="max-h-72 overflow-auto bg-ink-900/90 p-3 font-mono text-[11px] leading-relaxed text-zinc-300">
            {busy ? "loading…" : content}
          </pre>
        </div>
      )}
    </Panel>
  );
}
