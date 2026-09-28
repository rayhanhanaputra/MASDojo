import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorText } from "../components/ui";
import { AuthShell } from "./LoginPage";

export function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      await register(email, displayName, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Create an account" subtitle="Self-hosted and free. Your progress stays on your server.">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label" htmlFor="reg-name">
            Display name
          </label>
          <input
            id="reg-name"
            className="input"
            autoComplete="nickname"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div>
          <label className="label" htmlFor="reg-email">
            Email
          </label>
          <input
            id="reg-email"
            className="input"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label" htmlFor="reg-password">
            Password
          </label>
          <input
            id="reg-password"
            className="input"
            type="password"
            autoComplete="new-password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <p className="mt-1.5 font-mono text-2xs text-zinc-500">at least 8 characters</p>
        </div>
        {error && <ErrorText>{error}</ErrorText>}
        <button className="btn-primary w-full py-2.5" disabled={busy}>
          {busy ? "creating…" : "Register"}
          {!busy && <span aria-hidden>→</span>}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-zinc-400">
        Already registered?{" "}
        <Link to="/login" className="rounded font-medium text-phosphor hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
