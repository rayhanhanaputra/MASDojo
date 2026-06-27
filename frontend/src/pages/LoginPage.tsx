import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorText } from "../components/ui";

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

  return <AuthShell title="Access the dojo" subtitle="Sign in to continue your path.">
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label className="label">Email</label>
        <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
      </div>
      <div>
        <label className="label">Password</label>
        <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      {error && <ErrorText>{error}</ErrorText>}
      <button className="btn-primary w-full" disabled={busy}>
        {busy ? "authenticating…" : "Sign in"}
      </button>
    </form>
    <p className="mt-5 text-center text-sm text-zinc-500">
      No account?{" "}
      <Link to="/register" className="text-phosphor hover:underline">
        Register
      </Link>
    </p>
  </AuthShell>;
}

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
    <div className="grid min-h-full place-items-center px-5 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <h1 className="font-mono text-2xl font-bold">
            <span className="text-phosphor">MAS</span>Dojo
          </h1>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-widest text-zinc-600">
            mobile app security dojo
          </p>
        </div>
        <div className="panel p-6 shadow-glow">
          <h2 className="mb-1 text-lg font-semibold text-zinc-100">{title}</h2>
          <p className="mb-5 text-sm text-zinc-500">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  );
}
