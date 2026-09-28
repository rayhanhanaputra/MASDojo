import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Wordmark } from "./ui";

const navItems = [
  { to: "/", label: "Skill map", end: true },
  { to: "/profile", label: "Profile" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  const { user, logout, soloMode } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-20 border-b border-ink-500/60 bg-ink-900/80 backdrop-blur-md">
        {/* phosphor hairline on the very top edge */}
        <div aria-hidden className="h-px w-full bg-gradient-to-r from-transparent via-phosphor/60 to-transparent" />
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-2.5">
          <Link to="/" className="flex items-center gap-3 rounded-md" aria-label="MASDojo home">
            <Wordmark />
            <span className="hidden items-center gap-2 border-l border-ink-400 pl-3 font-mono text-2xs uppercase text-zinc-500 sm:inline-flex">
              MASVS / MASTG dojo
            </span>
          </Link>

          <nav className="flex items-center gap-0.5" aria-label="primary">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `relative rounded-md px-3 py-1.5 text-sm transition-colors ${
                    isActive
                      ? "text-phosphor after:absolute after:inset-x-3 after:-bottom-[11px] after:h-0.5 after:rounded-full after:bg-phosphor"
                      : "text-zinc-400 hover:bg-ink-700/70 hover:text-zinc-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            {!soloMode && (
              <button
                className="ml-2 inline-flex items-center gap-2 rounded-md border border-transparent px-3 py-1.5 font-mono text-xs text-zinc-400 transition-colors hover:border-signal-red/40 hover:text-signal-red"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
                title="Sign out"
              >
                <span className="hidden max-w-[10rem] truncate sm:inline">{user?.display_name}</span>
                <span aria-hidden className="text-zinc-600">·</span>
                logout
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 animate-rise">
        <Outlet />
      </main>

      <footer className="border-t border-ink-500/40">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-5 py-4 font-mono text-2xs uppercase text-zinc-500">
          <span>MASDojo · OWASP MASVS / MASTG</span>
          <span className="inline-flex items-center gap-1.5">
            <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-phosphor" />
            graded on a real Android emulator
          </span>
        </div>
      </footer>
    </div>
  );
}
