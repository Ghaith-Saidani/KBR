import { Link } from "react-router-dom";

import {
  useCurrentUser,
  useLogout,
} from "../features/auth/auth.hooks";

export default function AccountPage() {
  const logout = useLogout();

  const {
    data: user,
    isLoading,
    isError,
  } = useCurrentUser();

  if (isLoading) {
    return (
      <section className="flex min-h-[60vh] items-center justify-center bg-[#050505]">
        <div className="text-sm text-slate-400">
          Loading your account...
        </div>
      </section>
    );
  }

  if (isError || !user) {
    return (
      <section className="flex min-h-[60vh] items-center justify-center bg-[#050505] px-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">
            Session expired
          </h1>

          <p className="mt-3 text-slate-400">
            Please sign in again.
          </p>

          <Link
            to="/login"
            className="mt-6 inline-block rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black"
          >
            Sign in
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-[70vh] bg-[#050505] px-6 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
            Member area
          </p>

          <h1 className="mt-3 text-4xl font-black text-white">
            My account
          </h1>

          <p className="mt-3 text-slate-400">
            Manage your KBR account and membership.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <p className="text-sm text-slate-500">
              Email
            </p>

            <p className="mt-2 break-all text-lg font-semibold text-white">
              {user.email}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <p className="text-sm text-slate-500">
              Role
            </p>

            <p className="mt-2 text-lg font-semibold capitalize text-white">
              {user.role}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <p className="text-sm text-slate-500">
              Account status
            </p>

            <p className="mt-2 text-lg font-semibold capitalize text-white">
              {user.status}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <p className="text-sm text-slate-500">
              Email verification
            </p>

            <p className="mt-2 text-lg font-semibold text-white">
              {user.is_email_verified
                ? "Verified"
                : "Not verified"}
            </p>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            to="/"
            className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/5"
          >
            Back to home
          </Link>

          <button
            type="button"
            onClick={logout}
            className="rounded-xl bg-red-500/10 px-5 py-3 text-sm font-semibold text-red-300 transition hover:bg-red-500/20"
          >
            Sign out
          </button>
        </div>
      </div>
    </section>
  );
}