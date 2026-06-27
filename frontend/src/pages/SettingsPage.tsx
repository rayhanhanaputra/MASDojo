import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import type { ApiKeyStatus, Provider } from "../api/types";
import { ErrorText, Panel, Spinner } from "../components/ui";

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

  if (!status) return <Spinner label="loading settings…" />;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-100">Settings</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Bring your own AI key to unlock the adaptive mentor. Your key is validated, encrypted at
          rest, used only server-side, never shown again, and deletable at any time. The dojo and
          its grader work fully without a key.
        </p>
      </div>

      <Panel className="space-y-4">
        <h2 className="label">AI mentor key (BYOK)</h2>

        {status.configured ? (
          <div className="flex items-center justify-between rounded-md border border-phosphor/30 bg-phosphor/5 px-4 py-3">
            <div>
              <p className="text-sm text-zinc-200">
                <span className="font-mono text-phosphor">{status.provider}</span> key configured
              </p>
              <p className="font-mono text-xs text-zinc-500">
                {status.masked_key}
                {status.last_validated_at &&
                  ` · validated ${new Date(status.last_validated_at).toLocaleDateString()}`}
              </p>
            </div>
            <button className="btn-ghost text-xs text-signal-red" onClick={remove} disabled={busy}>
              Remove
            </button>
          </div>
        ) : (
          <p className="rounded-md border border-ink-500 bg-ink-900/50 px-4 py-3 text-sm text-zinc-500">
            No key configured — AI features are disabled. The grader still works.
          </p>
        )}

        <form onSubmit={save} className="space-y-3">
          <div className="flex gap-3">
            <div className="w-40">
              <label className="label">Provider</label>
              <select
                className="input"
                value={provider}
                onChange={(e) => setProvider(e.target.value as Provider)}
              >
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="label">API key</label>
              <input
                className="input font-mono"
                type="password"
                placeholder={provider === "anthropic" ? "sk-ant-…" : "sk-…"}
                value={key}
                onChange={(e) => setKey(e.target.value)}
                required
              />
            </div>
          </div>
          {error && <ErrorText>{error}</ErrorText>}
          {ok && <p className="font-mono text-sm text-phosphor">{ok}</p>}
          <button className="btn-primary" disabled={busy || !key.trim()}>
            {busy ? "validating…" : "Test & save"}
          </button>
        </form>
      </Panel>
    </div>
  );
}
