import { useState } from "react";
import type { FormEvent } from "react";

import { Link, useNavigate } from "react-router-dom";

import AuthLayout from "../components/auth/AuthLayout";
import { useRegister } from "../features/auth/auth.hooks";

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
    "Unable to create your account."
  );
}

export default function RegisterPage() {
  const navigate = useNavigate();

  const registerMutation = useRegister();

  const [firstName, setFirstName] =
    useState("");

  const [lastName, setLastName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [phone, setPhone] =
    useState("");

  const [validationError, setValidationError] =
    useState<string | null>(null);

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setValidationError(null);

    if (password !== confirmPassword) {
      setValidationError(
        "Passwords do not match.",
      );

      return;
    }

    registerMutation.mutate(
      {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
        phone: phone.trim() || undefined,
      },
      {
        onSuccess: () => {
          navigate("/login", {
            replace: true,
            state: {
              registered: true,
            },
          });
        },
      },
    );
  }

  return (
    <AuthLayout
      title="Join KBR"
      subtitle="Create your KBR member account."
    >
      <form
        onSubmit={handleSubmit}
        className="space-y-5"
      >
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <label
              htmlFor="firstName"
              className="mb-2 block text-sm font-medium text-slate-200"
            >
              First name
            </label>

            <input
              id="firstName"
              type="text"
              autoComplete="given-name"
              required
              minLength={2}
              value={firstName}
              onChange={(event) =>
                setFirstName(event.target.value)
              }
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
            />
          </div>

          <div>
            <label
              htmlFor="lastName"
              className="mb-2 block text-sm font-medium text-slate-200"
            >
              Last name
            </label>

            <input
              id="lastName"
              type="text"
              autoComplete="family-name"
              required
              minLength={2}
              value={lastName}
              onChange={(event) =>
                setLastName(event.target.value)
              }
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
            />
          </div>
        </div>

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
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>

        <div>
          <label
            htmlFor="phone"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Phone{" "}
            <span className="text-slate-500">
              (optional)
            </span>
          </label>

          <input
            id="phone"
            type="tel"
            autoComplete="tel"
            value={phone}
            onChange={(event) =>
              setPhone(event.target.value)
            }
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
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
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            placeholder="At least 8 characters"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Confirm password
          </label>

          <input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={confirmPassword}
            onChange={(event) =>
              setConfirmPassword(
                event.target.value,
              )
            }
            placeholder="Repeat your password"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>

        {(validationError ||
          registerMutation.isError) && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm leading-5 text-red-300">
            {validationError ??
              getErrorMessage(
                registerMutation.error,
              )}
          </div>
        )}

        <div className="rounded-xl border border-[#f5c400]/20 bg-[#f5c400]/5 px-4 py-3 text-sm leading-5 text-slate-300">
          New accounts require activation before
          you can sign in.
        </div>

        <button
          type="submit"
          disabled={registerMutation.isPending}
          className="w-full rounded-xl bg-[#f5c400] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#ffd426] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {registerMutation.isPending
            ? "Creating account..."
            : "Create account"}
        </button>
      </form>

      <div className="mt-6 border-t border-white/10 pt-6 text-center text-sm text-slate-400">
        Already have an account?{" "}
        <Link
          to="/login"
          className="font-semibold text-[#f5c400] transition hover:text-[#ffd426]"
        >
          Sign in
        </Link>
      </div>
    </AuthLayout>
  );
}