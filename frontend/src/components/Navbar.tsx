import { NavLink, useNavigate } from "react-router-dom";
import { clearToken } from "../lib/auth";

function navLinkClass({ isActive }: { isActive: boolean }) {
  return [
    "rounded-lg px-3 py-1.5 text-sm transition",
    isActive
      ? "bg-slate-800 text-slate-100"
      : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200",
  ].join(" ");
}

export default function Navbar({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 px-6 py-4">
        <span className="font-semibold">AI Cloud Cost Detective</span>
        <nav className="flex flex-wrap items-center gap-2">
          <NavLink to="/" end className={navLinkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/history" className={navLinkClass}>
            History
          </NavLink>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 transition hover:bg-slate-800"
          >
            Log out
          </button>
        </nav>
      </header>
      {children}
    </div>
  );
}
