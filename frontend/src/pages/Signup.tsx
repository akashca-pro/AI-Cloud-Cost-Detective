import { Link, useNavigate } from "react-router-dom";
import AuthForm from "../components/AuthForm";
import { api } from "../lib/api";
import { setToken } from "../lib/auth";

export default function Signup() {
  const navigate = useNavigate();

  async function handleSignup(email: string, password: string) {
    const { token } = await api.signup({ email, password });
    setToken(token);
    navigate("/", { replace: true });
  }

  return (
    <AuthForm
      title="Create account"
      submitLabel="Sign up"
      onSubmit={handleSignup}
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300">
            Log in
          </Link>
        </>
      }
    />
  );
}
