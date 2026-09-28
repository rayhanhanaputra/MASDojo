import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";
import { Certificate } from "../components/ProofCard";
import { Wordmark } from "../components/ui";

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
    <div className="mx-auto max-w-2xl px-5 py-12 animate-rise">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/" className="rounded" aria-label="MASDojo home">
          <Wordmark />
        </Link>
        <span className="font-mono text-2xs uppercase text-zinc-500">public verifier · no account needed</span>
      </div>

      <div className="mt-8">
        <p className="eyebrow">
          <span aria-hidden>✦ </span>Proof-of-Pwn
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
          Verify a certificate
        </h1>
        <p className="mt-2 max-w-xl text-sm text-zinc-400">
          Paste a certificate token to check that this server issued it and it hasn't been altered.
          Certificates are HMAC-signed by the grader at the moment a task passes.
        </p>
      </div>

      <div className="panel mt-6 p-5">
        <label className="label" htmlFor="cert-token">
          certificate token
        </label>
        <textarea
          id="cert-token"
          className="input h-32 w-full font-mono text-xs"
          placeholder="paste certificate token…"
          value={token}
          spellCheck={false}
          onChange={(e) => setToken(e.target.value)}
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <span className="font-mono text-2xs uppercase text-zinc-500">
            checks signature + evidence digest
          </span>
          <button className="btn-primary" disabled={busy || !token.trim()} onClick={verify}>
            {busy ? "verifying…" : "Verify"}
          </button>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded-md border border-signal-red/30 bg-signal-red/5 px-3 py-2 font-mono text-xs text-signal-red" role="alert">
          ✕ {error}
        </p>
      )}

      {result && result.valid && p && (
        <div className="animate-rise">
          <Certificate
            payload={p}
            digest={String(p.evidence_sha256 ?? "")}
            verified={true}
          />
        </div>
      )}

      {result && !result.valid && (
        <div className="reticle reticle-red mt-5 rounded-xl border border-signal-red/50 bg-signal-red/5 p-5 animate-rise" role="status">
          <div className="flex items-center gap-4">
            <span className="seal seal-invalid" role="img" aria-label="invalid">
              ✕
            </span>
            <div>
              <p className="font-mono text-base font-bold uppercase tracking-[0.2em] text-signal-red">
                invalid
              </p>
              <p className="mt-1 text-sm text-zinc-300">
                This server did not issue that certificate, or it has been tampered with.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
