import { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import { api } from "../api/endpoints";
import { API_BASE, getToken } from "../api/client";
import { ErrorText, Spinner } from "./ui";

function wsUrl(sessionId: number): string {
  const base = API_BASE.replace(/^http/, "ws");
  const token = getToken();
  const q = token ? `&token=${encodeURIComponent(token)}` : "";
  return `${base}/lab/terminal?session_id=${sessionId}${q}`;
}

/** A live in-browser terminal wired to a lab session's PTY over a WebSocket. */
export function LabTerminal({ taskId, onClose }: { taskId: string; onClose: () => void }) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState("");
  const [connecting, setConnecting] = useState(true);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [view, setView] = useState<"terminal" | "screen">("terminal");

  useEffect(() => {
    let term: Terminal | null = null;
    let ws: WebSocket | null = null;
    let fit: FitAddon | null = null;
    let disposed = false;

    (async () => {
      try {
        const session = await api.labStartSession(taskId);
        if (disposed) return;
        setStreamUrl(session.stream_url ?? null);
        if (!hostRef.current) return;

        term = new Terminal({
          fontSize: 13,
          fontFamily: "'JetBrains Mono', ui-monospace, monospace",
          theme: { background: "#0a0e0a", foreground: "#c8f7c8", cursor: "#39ff14" },
          cursorBlink: true,
          convertEol: true,
        });
        fit = new FitAddon();
        term.loadAddon(fit);
        term.open(hostRef.current);
        fit.fit();

        ws = new WebSocket(wsUrl(session.id));
        ws.onopen = () => {
          setConnecting(false);
          sendResize();
        };
        ws.onmessage = (ev) => term?.write(typeof ev.data === "string" ? ev.data : "");
        ws.onclose = () => term?.write("\r\n\x1b[90m[lab] disconnected\x1b[0m\r\n");
        ws.onerror = () => setError("WebSocket error. Is the lab enabled on the server?");

        term.onData((d) => ws?.readyState === WebSocket.OPEN && ws.send(d));

        function sendResize() {
          if (!term || !ws || ws.readyState !== WebSocket.OPEN) return;
          ws.send(`\x00resize:${term.cols},${term.rows}`);
        }
        const onResize = () => {
          fit?.fit();
          sendResize();
        };
        window.addEventListener("resize", onResize);
        // store for cleanup
        (term as unknown as { _onResize: () => void })._onResize = onResize;
      } catch (e) {
        if (!disposed) setError(e instanceof Error ? e.message : "Could not start lab session");
      }
    })();

    return () => {
      disposed = true;
      const onResize = (term as unknown as { _onResize?: () => void })?._onResize;
      if (onResize) window.removeEventListener("resize", onResize);
      ws?.close();
      term?.dispose();
    };
  }, [taskId]);

  async function stop() {
    try {
      await api.labEndSession();
    } catch {
      /* ignore */
    }
    onClose();
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {(["terminal", "screen"] as const).map((v) => (
            <button
              key={v}
              className={`rounded-md px-2.5 py-1 font-mono text-2xs uppercase ${
                view === v ? "bg-ink-700 text-phosphor" : "text-zinc-500"
              }`}
              onClick={() => setView(v)}
            >
              {v === "terminal" ? "terminal · adb/frida" : "device screen"}
            </button>
          ))}
        </div>
        <button className="btn-ghost btn-sm" onClick={stop}>
          End session
        </button>
      </div>
      {error && <ErrorText>{error}</ErrorText>}

      {/* Terminal host stays mounted (hidden, not unmounted) so xterm survives
          tab switches. */}
      <div
        className={`relative rounded-lg border border-ink-500/60 bg-[#0a0e0a] p-2 ${
          view === "terminal" ? "" : "hidden"
        }`}
      >
        {connecting && !error && (
          <div className="absolute inset-0 z-10 grid place-items-center bg-[#0a0e0a]/80">
            <Spinner label="connecting to lab…" />
          </div>
        )}
        <div ref={hostRef} className="h-80 w-full" />
      </div>

      {view === "screen" &&
        (streamUrl ? (
          <iframe
            title="device screen"
            src={streamUrl}
            className="h-96 w-full rounded-lg border border-ink-500/60 bg-black"
          />
        ) : (
          <div className="grid h-80 place-items-center rounded-lg border border-dashed border-ink-400 bg-ink-900/40 p-6 text-center">
            <div>
              <p className="text-sm text-zinc-300">No device screen available</p>
              <p className="mt-1 font-mono text-xs text-zinc-500">
                The visual emulator view needs a KVM runner with a live device and
                LAB_STREAM_URL configured (scrcpy-web / emulator WebRTC). The terminal works
                regardless.
              </p>
            </div>
          </div>
        ))}

      <p className="font-mono text-2xs text-zinc-600">
        Develop your exploit here, then submit it above. The grader verifies it on a clean device.
      </p>
    </div>
  );
}
