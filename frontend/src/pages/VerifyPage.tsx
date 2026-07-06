import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";

// Public Proof-of-Pwn verifier. Anyone — no account needed — can paste a
// certificate token to check whether THIS server issued it and it is untampered.
// Backs the /verify feature; the endpoint is intentionally unauthenticated.
export function VerifyPage() {
  const [token, setToken] = useState("");
  const [result, setResult] = useState<
    { valid: boolean; payload: Record<string, unknown> | null } | null
  >(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function verify() {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.verifyCertificate(token.trim()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "verification failed");
    } finally {
      setBusy(false);
    }
  }

  const p = result?.payload;

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Link to="/" className="font-mono text-xs text-zinc-500 hover:text-phosphor">
        ← MASDojo
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-zinc-100">Verify a Proof-of-Pwn</h1>
      <p className="mt-2 text-sm text-zinc-400">
        Paste a certificate token to check that this server issued it and it hasn't been altered.
        No account required.
      </p>

      <textarea
        className="input mt-6 h-32 w-full font-mono text-xs"
        placeholder="paste certificate token…"
        value={token}
        onChange={(e) => setToken(e.target.value)}
      />
      <button className="btn mt-3" disabled={busy || !token.trim()} onClick={verify}>
        {busy ? "verifying…" : "Verify"}
      </button>

      {error && <p className="mt-4 font-mono text-xs text-signal-red">{error}</p>}

      {result && (
        <div
          className={`mt-6 rounded-md border p-4 ${
            result.valid
              ? "border-phosphor/40 bg-phosphor/5"
              : "border-signal-red/40 bg-signal-red/5"
          }`}
        >
          <p
            className={`font-mono text-sm ${
              result.valid ? "text-phosphor" : "text-signal-red"
            }`}
          >
            {result.valid ? "✓ Valid certificate" : "✗ Invalid or tampered certificate"}
          </p>
          {result.valid && p && (
            <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-[11px] text-zinc-400">
              <dt className="text-zinc-600">learner</dt>
              <dd className="text-zinc-200">{String(p.learner)}</dd>
              <dt className="text-zinc-600">task</dt>
              <dd className="text-zinc-200">{String(p.task_title)}</dd>
              <dt className="text-zinc-600">score</dt>
              <dd className="text-phosphor">{String(p.score)} pts</dd>
              <dt className="text-zinc-600">evidence</dt>
              <dd className="truncate text-zinc-200" title={String(p.evidence_sha256 ?? "")}>
                sha256:{String(p.evidence_sha256 ?? "").slice(0, 16)}…
              </dd>
              <dt className="text-zinc-600">issued</dt>
              <dd className="text-zinc-200">{String(p.issued_at)}</dd>
            </dl>
          )}
        </div>
      )}
    </div>
  );
}
