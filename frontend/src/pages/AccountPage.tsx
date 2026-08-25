import {
  type FormEvent,
  useState,
} from "react";

import { Link } from "react-router-dom";

import {
  useCurrentUser,
  useLogout,
} from "../features/auth/auth.hooks";

import {
  useMyMemberProfile,
  useUpdateMyMemberProfile,
} from "../features/members/members.hooks";

import type { MemberProfile } from "../features/members/members.types";

interface MemberProfileFormProps {
  member: MemberProfile;
}

function MemberProfileForm({
  member,
}: MemberProfileFormProps) {
  const updateProfile =
    useUpdateMyMemberProfile();

  const [firstName, setFirstName] =
    useState(member.first_name);

  const [lastName, setLastName] =
    useState(member.last_name);

  const [position, setPosition] =
    useState(member.position ?? "");

  const [phone, setPhone] =
    useState(member.phone ?? "");

  const [profileImage, setProfileImage] =
    useState(member.profile_image ?? "");

  const [bio, setBio] =
    useState(member.bio ?? "");

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    updateProfile.mutate({
      first_name: firstName,
      last_name: lastName,
      position: position || null,
      phone: phone || null,
      profile_image: profileImage || null,
      bio: bio || null,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8"
    >
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white">
          Member profile
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          These details are displayed on your
          public KBR member profile.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label
            htmlFor="first-name"
            className="mb-2 block text-sm font-semibold text-white"
          >
            First name
          </label>

          <input
            id="first-name"
            type="text"
            value={firstName}
            onChange={(event) =>
              setFirstName(event.target.value)
            }
            minLength={2}
            maxLength={100}
            required
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]"
          />
        </div>

        <div>
          <label
            htmlFor="last-name"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Last name
          </label>

          <input
            id="last-name"
            type="text"
            value={lastName}
            onChange={(event) =>
              setLastName(event.target.value)
            }
            minLength={2}
            maxLength={100}
            required
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]"
          />
        </div>

        <div>
          <label
            htmlFor="position"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Position
          </label>

          <input
            id="position"
            type="text"
            value={position}
            onChange={(event) =>
              setPosition(event.target.value)
            }
            maxLength={150}
            placeholder="e.g. Player, Coach, Staff"
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]"
          />
        </div>

        <div>
          <label
            htmlFor="phone"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Phone
          </label>

          <input
            id="phone"
            type="tel"
            value={phone}
            onChange={(event) =>
              setPhone(event.target.value)
            }
            maxLength={30}
            placeholder="+216 ..."
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]"
          />
        </div>

        <div className="sm:col-span-2">
          <label
            htmlFor="profile-image"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Profile image URL
          </label>

          <input
            id="profile-image"
            type="url"
            value={profileImage}
            onChange={(event) =>
              setProfileImage(event.target.value)
            }
            maxLength={500}
            placeholder="https://..."
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]"
          />
        </div>

        <div className="sm:col-span-2">
          <label
            htmlFor="bio"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Bio
          </label>

          <textarea
            id="bio"
            value={bio}
            onChange={(event) =>
              setBio(event.target.value)
            }
            maxLength={2000}
            rows={6}
            placeholder="Tell the KBR community a little about yourself..."
            className="w-full resize-none rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <p className="mt-2 text-right text-xs text-slate-600">
            {bio.length}/2000
          </p>
        </div>
      </div>

      {updateProfile.isError && (
        <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Unable to update your profile.
          Please check your information and
          try again.
        </div>
      )}

      {updateProfile.isSuccess && (
        <div className="mt-6 rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm text-green-300">
          Your profile has been updated
          successfully.
        </div>
      )}

      <div className="mt-8 flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={updateProfile.isPending}
          className="rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-[#050505] transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {updateProfile.isPending
            ? "Saving..."
            : "Save changes"}
        </button>

        <Link
          to={`/members/${member.slug}`}
          className="rounded-xl border border-white/10 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/5"
        >
          View public profile
        </Link>
      </div>
    </form>
  );
}

export default function AccountPage() {
  const logout = useLogout();

  const {
    data: user,
    isLoading: isUserLoading,
    isError: isUserError,
  } = useCurrentUser();

  const {
    data: member,
    isLoading: isMemberLoading,
    isError: isMemberError,
  } = useMyMemberProfile(Boolean(user));

  if (
    isUserLoading ||
    isMemberLoading
  ) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505]">
        <div className="text-sm text-slate-400">
          Loading your account...
        </div>
      </section>
    );
  }

  if (isUserError || !user) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505] px-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">
            Session expired
          </h1>

          <p className="mt-3 text-slate-400">
            Please sign in again.
          </p>

          <Link
            to="/login"
            className="mt-6 inline-block rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            Sign in
          </Link>
        </div>
      </section>
    );
  }

  if (isMemberError || !member) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505] px-6">
        <div className="max-w-md text-center">
          <h1 className="text-2xl font-bold text-white">
            Member profile unavailable
          </h1>

          <p className="mt-3 text-slate-400">
            Your account is authenticated, but your
            KBR member profile could not be loaded.
          </p>

          <div className="mt-6 flex justify-center gap-3">
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

  return (
    <section className="min-h-[70vh] bg-[#050505] px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
            Member area
          </p>

          <h1 className="mt-3 text-4xl font-black text-white">
            My account
          </h1>

          <p className="mt-3 max-w-2xl text-slate-400">
            Manage your KBR account and public member
            profile.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
          <MemberProfileForm
            key={member.id}
            member={member}
          />

          <aside className="space-y-6">
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="text-lg font-bold text-white">
                Account
              </h2>

              <div className="mt-6 space-y-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Email
                  </p>

                  <p className="mt-1 break-all text-sm font-semibold text-white">
                    {user.email}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Role
                  </p>

                  <p className="mt-1 text-sm font-semibold capitalize text-white">
                    {user.role}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Account status
                  </p>

                  <p className="mt-1 text-sm font-semibold capitalize text-white">
                    {user.status}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Email verification
                  </p>

                  <p className="mt-1 text-sm font-semibold text-white">
                    {user.is_email_verified
                      ? "Verified"
                      : "Not verified"}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="text-lg font-bold text-white">
                Membership
              </h2>

              <div className="mt-6 space-y-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Member status
                  </p>

                  <p className="mt-1 text-sm font-semibold capitalize text-white">
                    {member.status}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Member since
                  </p>

                  <p className="mt-1 text-sm font-semibold text-white">
                    {member.joined_at
                      ? new Date(
                          member.joined_at,
                        ).toLocaleDateString(
                          "fr-FR",
                          {
                            day: "numeric",
                            month: "long",
                            year: "numeric",
                          },
                        )
                      : "Not specified"}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Public profile
                  </p>

                  <p className="mt-1 break-all text-sm text-slate-400">
                    /members/{member.slug}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
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
          </aside>
        </div>
      </div>
    </section>
  );
}