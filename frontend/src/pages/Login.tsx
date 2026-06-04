import { Link, useNavigate } from "react-router-dom";
import AuthForm from "../components/AuthForm";
import { api } from "../lib/api";
import { setToken } from "../lib/auth";

export default function Login() {
  const navigate = useNavigate();

  async function handleLogin(email: string, password: string) {
    const { token } = await api.login({ email, password });
    setToken(token);
    navigate("/", { replace: true });
  }

  return (
    <AuthForm
      title="Log in"
      submitLabel="Log in"
      onSubmit={handleLogin}
      footer={
        <>
          No account?{" "}
          <Link to="/signup" className="text-indigo-400 hover:text-indigo-300">
            Sign up
          </Link>
        </>
      }
    />
  );
}
