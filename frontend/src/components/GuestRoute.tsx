import { Navigate } from "react-router-dom";
import { isAuthenticated } from "../lib/auth";

/** Redirect logged-in users away from login/signup pages. */
export default function GuestRoute({ children }: { children: React.ReactNode }) {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
