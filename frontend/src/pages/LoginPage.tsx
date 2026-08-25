import { useState } from "react";
import { useEffect } from "react";
import type { FormEvent } from "react";

import { Link, useNavigate } from "react-router-dom";

import AuthLayout from "../components/auth/AuthLayout";
import { useAuthStore } from "../stores/authStore";
import { useLogin } from "../features/auth/auth.hooks";

function getErrorMessage(error: unknown): string {
  const axiosError = error as {
    response?: {
      data?: {
        detail?: string;
      };
    };
  };

  return (
    axiosError.response?.data?.detail ??
    "Unable to sign in. Please check your credentials."
  );
}

export default function LoginPage() {
  const navigate = useNavigate();

  const accessToken = useAuthStore(
    (state) => state.accessToken,
  );

  const loginMutation = useLogin();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (accessToken) {
      navigate("/account", {
        replace: true,
      });
    }
  }, [accessToken, navigate]);

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    loginMutation.mutate({
      email: email.trim(),
      password,
    });
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your KBR account."
    >
      <form
        onSubmit={handleSubmit}
        className="space-y-5"
      >
        <div>
          <label
            htmlFor="email"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Email
          </label>

          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            placeholder="you@example.com"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Password
          </label>

          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            placeholder="••••••••"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>

        {loginMutation.isError && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm leading-5 text-red-300">
            {getErrorMessage(
              loginMutation.error,
            )}
          </div>
        )}

        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="w-full rounded-xl bg-[#f5c400] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#ffd426] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loginMutation.isPending
            ? "Signing in..."
            : "Sign in"}
        </button>
      </form>

      <div className="mt-6 border-t border-white/10 pt-6 text-center text-sm text-slate-400">
        Don't have an account?{" "}
        <Link
          to="/register"
          className="font-semibold text-[#f5c400] transition hover:text-[#ffd426]"
        >
          Create one
        </Link>
      </div>
    </AuthLayout>
  );
}