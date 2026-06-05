import { useNavigate } from "react-router-dom";
import { clearToken } from "../lib/auth";

/** Temporary shell until Navbar lands (devanarayan, WP5). */
export default function AppShell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
        <span className="font-semibold">AI Cloud Cost Detective</span>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 transition hover:bg-slate-800"
        >
          Log out
        </button>
      </header>
      {children}
    </div>
  );
}
