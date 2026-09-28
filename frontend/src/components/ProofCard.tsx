import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";

// Proof-of-Pwn: a signed, server-verifiable PASS receipt (HMAC-signed by the
// grader). Renders on a passed submission and self-verifies via the public
// /verify endpoint — tamper-evident, answering "did THIS server issue this?".
export function ProofCard({ submissionId }: { submissionId: number }) {
  const [token, setToken] = useState("");
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [verified, setVerified] = useState<boolean | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .getCertificate(submissionId)
      .then(async (c) => {
        if (!alive) return;
        setToken(c.token);
        setPayload(c.payload);
        const v = await api.verifyCertificate(c.token);
        if (alive) setVerified(v.valid);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [submissionId]);

  if (!payload) return null;

  const digest = String(payload.evidence_sha256 ?? "");

  return (
    <Certificate
      payload={payload}
      digest={digest}
      verified={verified}
      footer={
        <div className="flex flex-wrap items-center gap-2">
          <button
            className="btn-ghost btn-sm flex-1"
            onClick={() => {
              navigator.clipboard?.writeText(token);
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1500);
            }}
          >
            {copied ? "copied ✓" : "copy certificate token"}
          </button>
          <Link to="/verify" className="btn-ghost btn-sm" target="_blank" rel="noreferrer">
            open /verify ↗
          </Link>
        </div>
      }
    />
  );
}

// The certificate surface itself. Shared with the public /verify page so a
// Proof-of-Pwn looks identical wherever it is rendered.
export function Certificate({
  payload,
  digest,
  verified,
  footer,
}: {
  payload: Record<string, unknown>;
  digest: string;
  verified: boolean | null;
  footer?: ReactNode;
}) {
  const invalid = verified === false;
  const fingerprint = digest.slice(0, 32).match(/.{1,4}/g) ?? [];

  return (
    <div
      className={`relative mt-5 overflow-hidden rounded-xl border p-[3px] ${
        invalid ? "border-signal-red/50" : "border-phosphor/50 shadow-glow"
      }`}
      role="group"
      aria-label="Proof-of-Pwn certificate"
    >
      {/* inner hairline frame — the "printed certificate" border */}
      <div className={`rounded-lg border border-dashed p-4 ${invalid ? "border-signal-red/30" : "border-phosphor/30 bg-phosphor/[0.03]"}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className={`font-mono text-2xs uppercase ${invalid ? "text-signal-red" : "text-phosphor"}`}>
              <span aria-hidden>✦ </span>Proof-of-Pwn
            </p>
            <p className="mt-0.5 text-[15px] font-semibold tracking-tight text-zinc-50">
              {String(payload.task_title)}
            </p>
            <p className="mt-0.5 font-mono text-xs text-zinc-400">
              cleared by <span className="text-zinc-100">{String(payload.learner)}</span>
            </p>
          </div>
          <div className="flex flex-col items-center gap-1">
            <span className={`seal ${invalid ? "seal-invalid" : ""}`} role="img" aria-label={invalid ? "signature invalid" : verified ? "signature verified" : "signature pending"}>
              {invalid ? "✕" : "✓"}
            </span>
            <span className={`font-mono text-2xs uppercase ${invalid ? "text-signal-red" : verified ? "text-phosphor" : "text-zinc-400"}`}>
              {invalid ? "invalid" : verified ? "verified" : "checking"}
            </span>
          </div>
        </div>

        <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 border-t border-ink-500/60 pt-3 font-mono text-xs">
          <dt className="text-zinc-400">score</dt>
          <dd className="font-bold text-phosphor">{String(payload.score)} pts</dd>
          <dt className="text-zinc-400">issued</dt>
          <dd className="truncate text-zinc-200">{String(payload.issued_at)}</dd>
          <dt className="text-zinc-400">evidence</dt>
          <dd className="min-w-0">
            <span className="block text-2xs uppercase text-zinc-400">sha256</span>
            <span className="grid grid-cols-4 gap-x-2 text-zinc-200 sm:grid-cols-8" title={digest}>
              {fingerprint.map((chunk, i) => (
                <span key={i} className={i % 2 === 0 ? "text-zinc-200" : "text-zinc-400"}>
                  {chunk}
                </span>
              ))}
              {digest.length > 32 && (
                <span className="text-zinc-500" aria-hidden>
                  …
                </span>
              )}
            </span>
          </dd>
        </dl>

        {footer && <div className="mt-4">{footer}</div>}
      </div>
    </div>
  );
}
