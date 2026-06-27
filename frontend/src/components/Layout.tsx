import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/profile", label: "Profile" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-20 border-b border-ink-500/60 bg-ink-900/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-phosphor">MAS</span>
            <span className="font-mono text-lg font-bold text-zinc-200">Dojo</span>
            <span className="ml-2 hidden font-mono text-[10px] uppercase tracking-widest text-zinc-600 sm:inline">
              mobile app security
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm transition-colors ${
                    isActive
                      ? "bg-ink-600 text-phosphor"
                      : "text-zinc-400 hover:text-zinc-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            <button
              className="ml-2 rounded-md px-3 py-1.5 text-sm text-zinc-500 hover:text-signal-red"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              {user?.display_name} · logout
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-ink-500/40 py-4 text-center font-mono text-[11px] text-zinc-700">
        defensive education · OWASP MASVS / MASTG aligned · graded on a real emulator
      </footer>
    </div>
  );
}
