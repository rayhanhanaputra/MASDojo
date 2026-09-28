import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorText, Wordmark } from "../components/ui";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Access the dojo" subtitle="Sign in to continue your path.">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            className="input"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div>
          <label className="label" htmlFor="login-password">
            Password
          </label>
          <input
            id="login-password"
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <ErrorText>{error}</ErrorText>}
        <button className="btn-primary w-full py-2.5" disabled={busy}>
          {busy ? "authenticating…" : "Sign in"}
          {!busy && <span aria-hidden>→</span>}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-zinc-400">
        No account?{" "}
        <Link to="/register" className="rounded font-medium text-phosphor hover:underline">
          Register
        </Link>
      </p>
    </AuthShell>
  );
}

const PILLARS = [
  { glyph: "▣", title: "Real emulator", body: "Every task is graded live on an Android AVD." },
  { glyph: "✦", title: "Proof-of-Pwn", body: "Each pass is a signed, verifiable certificate." },
  { glyph: "◆", title: "AI mentor", body: "Adaptive hints, never a served answer." },
];

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="relative grid min-h-full place-items-center overflow-hidden px-5 py-12">
      {/* ambient phosphor pool behind the card */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/3 h-[32rem] w-[32rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-phosphor/10 blur-3xl"
      />
      <div className="relative w-full max-w-sm animate-rise">
        <div className="mb-8 text-center">
          <Wordmark size="lg" />
          <p className="mt-3 font-mono text-2xs uppercase text-zinc-400">
            mobile app security dojo · MASVS / MASTG
          </p>
        </div>

        <div className="reticle panel p-6 shadow-glow-lg sm:p-7">
          <h2 className="text-lg font-semibold tracking-tight text-zinc-50">{title}</h2>
          <p className="mb-5 mt-1 text-sm text-zinc-400">{subtitle}</p>
          {children}
        </div>

        <ul className="mt-8 grid grid-cols-3 gap-3" aria-label="what MASDojo does">
          {PILLARS.map((p) => (
            <li key={p.title} className="text-center">
              <span aria-hidden className="font-mono text-base text-phosphor">
                {p.glyph}
              </span>
              <p className="mt-1 font-mono text-2xs uppercase text-zinc-200">{p.title}</p>
              <p className="mt-1 text-[11px] leading-snug text-zinc-500">{p.body}</p>
            </li>
          ))}
        </ul>

        <p className="mt-8 text-center font-mono text-2xs uppercase text-zinc-600">
          self-hosted · open source ·{" "}
          <Link to="/verify" className="rounded text-zinc-500 hover:text-phosphor">
            verify a certificate
          </Link>
        </p>
      </div>
    </div>
  );
}
