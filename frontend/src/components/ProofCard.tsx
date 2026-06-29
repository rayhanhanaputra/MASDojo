import { useEffect, useState } from "react";
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
    <div className="mt-4 rounded-md border border-phosphor/40 bg-phosphor/5 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-widest text-phosphor">
          ✦ Proof-of-Pwn
        </span>
        {verified === true && (
          <span className="font-mono text-[10px] text-phosphor">verified ✓ /verify</span>
        )}
        {verified === false && (
          <span className="font-mono text-[10px] text-signal-red">signature invalid</span>
        )}
      </div>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-[11px] text-zinc-400">
        <dt className="text-zinc-600">learner</dt>
        <dd className="text-zinc-200">{String(payload.learner)}</dd>
        <dt className="text-zinc-600">task</dt>
        <dd className="truncate text-zinc-200">{String(payload.task_title)}</dd>
        <dt className="text-zinc-600">score</dt>
        <dd className="text-phosphor">{String(payload.score)} pts</dd>
        <dt className="text-zinc-600">evidence</dt>
        <dd className="truncate text-zinc-200" title={digest}>
          sha256:{digest.slice(0, 16)}…
        </dd>
        <dt className="text-zinc-600">issued</dt>
        <dd className="truncate text-zinc-200">{String(payload.issued_at)}</dd>
      </dl>
      <button
        className="btn-ghost mt-3 w-full text-[11px]"
        onClick={() => {
          navigator.clipboard?.writeText(token);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1500);
        }}
      >
        {copied ? "copied ✓" : "copy certificate token"}
      </button>
    </div>
  );
}
