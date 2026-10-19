import { useEffect, useState } from "react";
import { api } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import type {
  InstanceConfig,
  LabSessionAdminView,
  Role,
  SystemCheckItem,
  UserAdminView,
} from "../api/types";
import { ErrorText, Modal, PageHeader, Panel, Skeleton } from "../components/ui";
import { StatsModal } from "../components/StatsModal";

const ROLES: Role[] = ["learner", "instructor", "admin"];

const STATUS_STYLE: Record<SystemCheckItem["status"], { dot: string; text: string; label: string }> = {
  ok: { dot: "bg-phosphor", text: "text-phosphor", label: "ok" },
  warn: { dot: "bg-signal-amber", text: "text-signal-amber", label: "warn" },
  down: { dot: "bg-signal-red", text: "text-signal-red", label: "down" },
  disabled: { dot: "bg-zinc-600", text: "text-zinc-500", label: "off" },
};

function SystemHealth() {
  const [checks, setChecks] = useState<SystemCheckItem[] | null>(null);
  const [error, setError] = useState("");

  function load() {
    api.adminSystemCheck().then(setChecks).catch((e) => setError(e.message));
  }
  useEffect(() => {
    load();
    const t = window.setInterval(load, 10000);
    return () => window.clearInterval(t);
  }, []);

  return (
    <Panel className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="label mb-0">System health</h2>
        <button className="btn-ghost btn-sm" onClick={load}>
          Refresh
        </button>
      </div>
      {error && <ErrorText>{error}</ErrorText>}
      {!checks ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          {checks.map((c) => {
            const s = STATUS_STYLE[c.status];
            return (
              <div
                key={c.component}
                className="flex items-start gap-3 rounded-lg border border-ink-400 bg-ink-900/50 px-3 py-2.5"
              >
                <span aria-hidden className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${s.dot}`} />
                <div className="min-w-0">
                  <p className="text-sm text-zinc-100">
                    {c.component.replace(/_/g, " ")}
                    <span className={`ml-2 font-mono text-2xs uppercase ${s.text}`}>{s.label}</span>
                  </p>
                  <p className="font-mono text-xs text-zinc-500">{c.detail}</p>
                  {c.hint && c.status !== "ok" && (
                    <p className="mt-1 font-mono text-2xs text-zinc-600">→ {c.hint}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Panel>
  );
}

function LabSessions() {
  const [sessions, setSessions] = useState<LabSessionAdminView[] | null>(null);
  const [error, setError] = useState("");

  function load() {
    api.adminLabSessions().then(setSessions).catch((e) => setError(e.message));
  }
  useEffect(() => {
    load();
    const t = window.setInterval(load, 10000);
    return () => window.clearInterval(t);
  }, []);

  return (
    <Panel className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="label mb-0">Active lab sessions</h2>
        <button className="btn-ghost btn-sm" onClick={load}>
          Refresh
        </button>
      </div>
      {error && <ErrorText>{error}</ErrorText>}
      {!sessions ? (
        <Skeleton className="h-12 w-full" />
      ) : sessions.length === 0 ? (
        <p className="text-sm text-zinc-500">No active sessions.</p>
      ) : (
        <ul className="divide-y divide-ink-700/50 font-mono text-xs">
          {sessions.map((s) => (
            <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <span className="text-zinc-200">{s.user_email}</span>
              <span className="text-zinc-500">{s.task_id}</span>
              <span className="text-phosphor">{s.device_serial ?? "placeholder shell"}</span>
              <span className="text-zinc-600">
                expires {new Date(s.expires_at).toLocaleTimeString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function InstanceSettings() {
  const [cfg, setCfg] = useState<InstanceConfig | null>(null);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(false);
  // AI fallback form
  const [provider, setProvider] = useState<"anthropic" | "openai">("openai");
  const [key, setKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  // Switch-to-hosted form (provisions a real admin)
  const [showHostedForm, setShowHostedForm] = useState(false);
  const [showSoloConfirm, setShowSoloConfirm] = useState(false);
  const [adminEmail, setAdminEmail] = useState("");
  const [adminName, setAdminName] = useState("");
  const [adminPass, setAdminPass] = useState("");
  // Device pool form (prefilled from cfg once loaded)
  const [emuImage, setEmuImage] = useState("");
  const [emuSerial, setEmuSerial] = useState("");
  const [emuPort, setEmuPort] = useState(5037);
  const [emuTimeout, setEmuTimeout] = useState(180);
  const [poolInit, setPoolInit] = useState(false);

  function load() {
    api
      .adminGetSettings()
      .then((c) => {
        setCfg(c);
        if (!poolInit) {
          setEmuImage(c.lab_emulator_image);
          setEmuSerial(c.lab_emulator_serial);
          setEmuPort(c.lab_emulator_adb_port);
          setEmuTimeout(c.lab_emulator_boot_timeout_sec);
          setPoolInit(true);
        }
      })
      .catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function act(fn: () => Promise<InstanceConfig>, okMsg: string) {
    setError("");
    setOk("");
    setBusy(true);
    try {
      setCfg(await fn());
      setOk(okMsg);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  if (!cfg) return <Skeleton className="h-32 w-full" />;

  return (
    <Panel className="space-y-4 border-signal-violet/25">
      <h2 className="label mb-0">Instance settings</h2>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-ink-400 bg-ink-900/50 px-4 py-3">
        <div>
          <p className="text-sm text-zinc-100">Operating mode</p>
          <p className="font-mono text-xs text-zinc-500">
            {cfg.solo_mode ? "solo: no login, single local profile" : "hosted: accounts and roles"}
          </p>
        </div>
        <button
          className="btn-ghost btn-sm"
          disabled={busy}
          onClick={() => (cfg.solo_mode ? setShowHostedForm(true) : setShowSoloConfirm(true))}
        >
          {cfg.solo_mode ? "Switch to hosted" : "Switch to solo"}
        </button>
      </div>

      {!cfg.solo_mode && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-ink-400 bg-ink-900/50 px-4 py-3">
          <div>
            <p className="text-sm text-zinc-100">Registration</p>
            <p className="font-mono text-xs text-zinc-500">
              {cfg.registration_open ? "open: anyone can sign up" : "closed: no new accounts"}
            </p>
          </div>
          <button
            className="btn-ghost btn-sm"
            disabled={busy}
            onClick={() =>
              act(
                () => api.adminUpdateSettings({ registration_open: !cfg.registration_open }),
                "Registration updated.",
              )
            }
          >
            {cfg.registration_open ? "Close" : "Open"}
          </button>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-ink-400 bg-ink-900/50 px-4 py-3">
        <div>
          <p className="text-sm text-zinc-100">
            Interactive lab ({cfg.solo_mode ? "local device" : "remote device"})
          </p>
          <p className="font-mono text-xs text-zinc-500">
            {cfg.lab_enabled
              ? cfg.solo_mode
                ? "enabled: terminal attaches to your own machine's device"
                : "enabled: terminal attaches to the runner's emulator"
              : "disabled: no live terminal"}
          </p>
        </div>
        <button
          className="btn-ghost btn-sm"
          disabled={busy}
          onClick={() =>
            act(
              () => api.adminUpdateSettings({ lab_enabled: !cfg.lab_enabled }),
              "Lab playground updated.",
            )
          }
        >
          {cfg.lab_enabled ? "Disable" : "Enable"}
        </button>
      </div>

      {!cfg.solo_mode && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-ink-400 bg-ink-900/50 px-4 py-3">
          <div>
            <p className="text-sm text-zinc-100">Lab device access (hosted)</p>
            <p className="font-mono text-xs text-zinc-500">
              {cfg.lab_allow_device_hosted
                ? "allowed: sessions get a live device when the KVM pool provides one (else static)"
                : "off: sessions are static analysis only (isolated, no device)"}
            </p>
          </div>
          <button
            className="btn-ghost btn-sm"
            disabled={busy}
            onClick={() =>
              act(
                () =>
                  api.adminUpdateSettings({
                    lab_allow_device_hosted: !cfg.lab_allow_device_hosted,
                  }),
                "Lab device access updated.",
              )
            }
          >
            {cfg.lab_allow_device_hosted ? "Disallow" : "Allow"}
          </button>
        </div>
      )}

      {!cfg.solo_mode && cfg.lab_allow_device_hosted && (
        <div className="space-y-3 rounded-lg border border-ink-400 bg-ink-900/50 px-4 py-3">
          <div>
            <p className="text-sm text-zinc-100">Device pool (KVM)</p>
            <p className="font-mono text-xs text-zinc-500">
              {cfg.lab_emulator_image
                ? `image: ${cfg.lab_emulator_image}`
                : "no emulator image set: sessions stay static until you configure one"}
            </p>
          </div>
          <form
            className="flex flex-wrap items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              act(
                () =>
                  api.adminUpdateSettings({
                    lab_emulator_image: emuImage.trim(),
                    lab_emulator_serial: emuSerial.trim() || "emulator-5554",
                    lab_emulator_adb_port: emuPort,
                    lab_emulator_boot_timeout_sec: emuTimeout,
                  }),
                "Device pool updated.",
              );
            }}
          >
            <div className="min-w-[16rem] flex-1">
              <label className="label" htmlFor="emu-image">Emulator image (empty = pool off)</label>
              <input id="emu-image" className="input font-mono" placeholder="budtmo/docker-android:emulator_14.0" value={emuImage} onChange={(e) => setEmuImage(e.target.value)} />
            </div>
            <div className="w-36">
              <label className="label" htmlFor="emu-serial">Serial</label>
              <input id="emu-serial" className="input font-mono" value={emuSerial} onChange={(e) => setEmuSerial(e.target.value)} />
            </div>
            <div className="w-24">
              <label className="label" htmlFor="emu-port">adb port</label>
              <input id="emu-port" className="input font-mono" type="number" min={1} max={65535} value={emuPort} onChange={(e) => setEmuPort(Number(e.target.value))} />
            </div>
            <div className="w-28">
              <label className="label" htmlFor="emu-timeout">boot (s)</label>
              <input id="emu-timeout" className="input font-mono" type="number" min={10} max={1800} value={emuTimeout} onChange={(e) => setEmuTimeout(Number(e.target.value))} />
            </div>
            <button className="btn-primary btn-sm" disabled={busy}>Save</button>
          </form>
          <p className="font-mono text-2xs text-zinc-600">
            Needs a KVM host (/dev/kvm). The image must run an adb server on the port above. Each
            session boots its own emulator on a private network.
          </p>
        </div>
      )}

      <div className="space-y-3 rounded-lg border border-ink-400 bg-ink-900/50 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm text-zinc-100">AI mentor fallback</p>
            <p className="font-mono text-xs text-zinc-500">
              {cfg.ai_fallback_configured
                ? `${cfg.ai_fallback_provider} · ${cfg.ai_fallback_masked} · ${cfg.ai_fallback_model ?? "default"}`
                : "none: users must bring their own key"}
            </p>
          </div>
          {cfg.ai_fallback_configured && (
            <button
              className="btn-ghost btn-sm text-signal-red hover:border-signal-red/60 hover:text-signal-red"
              disabled={busy}
              onClick={() => act(() => api.adminClearFallback(), "Fallback removed.")}
            >
              Remove
            </button>
          )}
        </div>
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            act(
              () => api.adminSetFallback(provider, key.trim(), baseUrl.trim(), model.trim()),
              "Fallback validated and stored (encrypted).",
            ).then(() => setKey(""));
          }}
        >
          <select className="input w-28 py-1" value={provider} onChange={(e) => setProvider(e.target.value as "anthropic" | "openai")}>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
          <input className="input w-36 font-mono" type="password" placeholder="api key" value={key} onChange={(e) => setKey(e.target.value)} />
          <input className="input w-44 font-mono" placeholder="base URL (optional)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
          <input className="input w-32 font-mono" placeholder="model" value={model} onChange={(e) => setModel(e.target.value)} />
          <button className="btn-primary btn-sm" disabled={busy || !key.trim()}>
            Save
          </button>
        </form>
      </div>

      {error && <ErrorText>{error}</ErrorText>}
      {ok && (
        <p className="rounded-md border border-phosphor/30 bg-phosphor/5 px-3 py-2 font-mono text-xs text-phosphor" role="status">
          {ok}
        </p>
      )}

      {showHostedForm && (
        <Modal title="Switch to hosted mode" onClose={() => setShowHostedForm(false)}>
          <p className="text-sm text-zinc-400">
            Hosted mode requires login. Create the admin account you will sign in with, or the
            instance would have no reachable admin.
          </p>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              act(
                () => api.adminSwitchToHosted(adminEmail.trim(), adminName.trim(), adminPass),
                "Switched to hosted. Reload, then log in with your new admin account.",
              ).then(() => setShowHostedForm(false));
            }}
          >
            <div>
              <label className="label" htmlFor="adm-email">Admin email</label>
              <input id="adm-email" className="input" type="email" required value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="adm-name">Display name</label>
              <input id="adm-name" className="input" required value={adminName} onChange={(e) => setAdminName(e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="adm-pass">Password</label>
              <input id="adm-pass" className="input font-mono" type="password" required minLength={8} value={adminPass} onChange={(e) => setAdminPass(e.target.value)} />
              <p className="mt-1 font-mono text-2xs text-zinc-600">at least 8 characters</p>
            </div>
            {error && <ErrorText>{error}</ErrorText>}
            <button className="btn-primary w-full" disabled={busy}>
              {busy ? "switching…" : "Create admin and switch to hosted"}
            </button>
          </form>
        </Modal>
      )}

      {showSoloConfirm && (
        <Modal title="Switch to solo mode" onClose={() => setShowSoloConfirm(false)}>
          <p className="text-sm text-zinc-400">
            Solo mode collapses the app to a single local profile with no login. Existing accounts
            stay in the database but are not used while solo mode is on.
          </p>
          {error && <ErrorText>{error}</ErrorText>}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost btn-sm" onClick={() => setShowSoloConfirm(false)}>
              Cancel
            </button>
            <button
              className="btn-primary btn-sm"
              disabled={busy}
              onClick={() =>
                act(() => api.adminSwitchToSolo(), "Switched to solo. Reload to apply.").then(() =>
                  setShowSoloConfirm(false),
                )
              }
            >
              Switch to solo
            </button>
          </div>
        </Modal>
      )}
    </Panel>
  );
}

export function AdminPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<UserAdminView[] | null>(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [statsUserId, setStatsUserId] = useState<number | null>(null);

  function load() {
    api.adminListUsers().then(setUsers).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function run(id: number, fn: () => Promise<unknown>) {
    setError("");
    setBusyId(id);
    try {
      await fn();
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  if (!users)
    return (
      <div className="mx-auto max-w-4xl space-y-6" role="status" aria-label="loading users">
        <Skeleton className="h-7 w-40" />
        <div className="panel space-y-3 p-5">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    );

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        eyebrow="admin"
        title="Users"
        subtitle="Manage accounts and roles. Learners solve tasks; instructors manage the task catalog; admins manage users. You can't lock yourself out: your own admin role and the last admin are protected."
      />
      {error && <ErrorText>{error}</ErrorText>}

      <SystemHealth />

      <LabSessions />

      <InstanceSettings />

      <Panel className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-500/60 text-left font-mono text-2xs uppercase text-zinc-500">
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const self = u.id === me?.id;
              const busy = busyId === u.id;
              return (
                <tr key={u.id} className="border-b border-ink-700/50 last:border-0">
                  <td className="px-4 py-3">
                    <div className="text-zinc-100">
                      {u.display_name}
                      {self && <span className="ml-2 font-mono text-2xs text-phosphor">you</span>}
                    </div>
                    <div className="font-mono text-xs text-zinc-500">{u.email}</div>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      className="input w-32 py-1"
                      value={u.role}
                      disabled={busy || self}
                      title={self ? "Use another admin to change your own role" : undefined}
                      onChange={(e) => run(u.id, () => api.adminSetRole(u.id, e.target.value as Role))}
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`font-mono text-xs ${u.is_active ? "text-phosphor" : "text-zinc-500"}`}
                    >
                      {u.is_active ? "active" : "disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <button className="btn-ghost btn-sm" onClick={() => setStatsUserId(u.id)}>
                        Stats
                      </button>
                      <button
                        className="btn-ghost btn-sm"
                        disabled={busy || self}
                        onClick={() => run(u.id, () => api.adminSetActive(u.id, !u.is_active))}
                      >
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                      <button
                        className="btn-ghost btn-sm text-signal-red hover:border-signal-red/60 hover:bg-signal-red/5 hover:text-signal-red"
                        disabled={busy || self}
                        onClick={() => run(u.id, () => api.adminDeleteUser(u.id))}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>

      {statsUserId !== null && (
        <StatsModal userId={statsUserId} onClose={() => setStatsUserId(null)} />
      )}
    </div>
  );
}
