import { useNavigate } from "react-router-dom";
import { clearToken } from "../lib/auth";

export default function Home() {
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
          onClick={handleLogout}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 transition hover:bg-slate-800"
        >
          Log out
        </button>
      </header>

      <main className="mx-auto max-w-2xl px-6 py-16 text-center">
        <h1 className="text-3xl font-semibold">You are logged in</h1>
        <p className="mt-3 text-slate-400">
          The Dashboard, Report, and History pages arrive in WP5. Authentication (WP4) is wired up.
        </p>
      </main>
    </div>
  );
}
