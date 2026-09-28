import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { ApiKeyStatus, Provider } from "../api/types";
import { ErrorText, MentorMark, PageHeader, Panel, Skeleton } from "../components/ui";

export function SettingsPage() {
  const [status, setStatus] = useState<ApiKeyStatus | null>(null);
  const [provider, setProvider] = useState<Provider>("anthropic");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  function load() {
    api.getAiKey().then(setStatus).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setOk("");
    setBusy(true);
    try {
      const s = await api.setAiKey(provider, key.trim());
      setStatus(s);
      setKey("");
      setOk("Key validated and stored (encrypted).");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save key");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setError("");
    setOk("");
    try {
      await api.deleteAiKey();
      setStatus({ configured: false, provider: null, masked_key: null, last_validated_at: null });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove key");
    } finally {
      setBusy(false);
    }
  }

  if (!status)
    return (
      <div className="mx-auto max-w-2xl space-y-6" role="status" aria-label="loading settings">
        <div className="space-y-2">
          <Skeleton className="h-7 w-32" />
          <Skeleton className="h-3.5 w-full max-w-lg" />
        </div>
        <div className="panel space-y-4 p-5">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        eyebrow="settings"
        title="Settings"
        subtitle="Bring your own AI key to unlock the adaptive mentor. Your key is validated, encrypted at rest, used only server-side, never shown again, and deletable at any time. The dojo and its grader work fully without a key."
      />

      <Panel className="space-y-4 border-signal-violet/25">
        <div className="flex items-center justify-between">
          <h2 className="label mb-0">AI mentor key (BYOK)</h2>
          <MentorMark />
        </div>

        {status.configured ? (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-phosphor/30 bg-phosphor/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <span
                aria-hidden
                className="grid h-8 w-8 place-items-center rounded-full bg-phosphor font-mono text-sm font-bold text-ink-900"
              >
                ✓
              </span>
              <div>
                <p className="text-sm text-zinc-100">
                  <span className="font-mono text-phosphor">{status.provider}</span> key configured
                </p>
                <p className="font-mono text-xs text-zinc-400">
                  {status.masked_key}
                  {status.last_validated_at &&
                    ` · validated ${new Date(status.last_validated_at).toLocaleDateString()}`}
                </p>
              </div>
            </div>
            <button
              className="btn-ghost btn-sm text-signal-red hover:border-signal-red/60 hover:bg-signal-red/5 hover:text-signal-red"
              onClick={remove}
              disabled={busy}
            >
              Remove
            </button>
          </div>
        ) : (
          <p className="flex items-start gap-3 rounded-lg border border-dashed border-ink-400 bg-ink-900/50 px-4 py-3 text-sm text-zinc-400">
            <span aria-hidden className="font-mono text-zinc-500">○</span>
            No key configured — AI features are disabled. The emulator grader still works.
          </p>
        )}

        <form onSubmit={save} className="space-y-3">
          <div className="flex flex-wrap gap-3">
            <div className="w-40">
              <label className="label" htmlFor="ai-provider">
                Provider
              </label>
              <select
                id="ai-provider"
                className="input"
                value={provider}
                onChange={(e) => setProvider(e.target.value as Provider)}
              >
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div className="min-w-[12rem] flex-1">
              <label className="label" htmlFor="ai-key">
                API key
              </label>
              <input
                id="ai-key"
                className="input font-mono"
                type="password"
                autoComplete="off"
                placeholder={provider === "anthropic" ? "sk-ant-…" : "sk-…"}
                value={key}
                onChange={(e) => setKey(e.target.value)}
                required
              />
            </div>
          </div>
          {error && <ErrorText>{error}</ErrorText>}
          {ok && (
            <p className="flex items-center gap-2 rounded-md border border-phosphor/30 bg-phosphor/5 px-3 py-2 font-mono text-xs text-phosphor" role="status">
              <span aria-hidden>✓</span>
              {ok}
            </p>
          )}
          <button className="btn-primary" disabled={busy || !key.trim()}>
            {busy ? "validating…" : "Test & save"}
          </button>
        </form>
      </Panel>
    </div>
  );
}
