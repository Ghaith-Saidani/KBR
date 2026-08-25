import {
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import AuthLayout from "../components/auth/AuthLayout";
import { useRegister } from "../features/auth/auth.hooks";


function getErrorMessage(
  error: unknown,
): string {
  const axiosError =
    error as {
      response?: {
        data?: {
          detail?: string;
        };
      };
    };

  return (
    axiosError.response?.data?.detail ??
    "Impossible de créer votre compte."
  );
}


export default function RegisterPage() {
  const navigate =
    useNavigate();

  const registerMutation =
    useRegister();


  const [
    firstName,
    setFirstName,
  ] = useState("");

  const [
    lastName,
    setLastName,
  ] = useState("");

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [
    phone,
    setPhone,
  ] = useState("");

  const [
    validationError,
    setValidationError,
  ] = useState<string | null>(
    null,
  );


  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setValidationError(null);


    if (
      password !==
      confirmPassword
    ) {
      setValidationError(
        "Les mots de passe ne correspondent pas.",
      );

      return;
    }


    if (
      firstName.trim().length === 0 ||
      lastName.trim().length === 0
    ) {
      setValidationError(
        "Veuillez renseigner votre prénom et votre nom.",
      );

      return;
    }


    registerMutation.mutate(
      {
        first_name:
          firstName.trim(),

        last_name:
          lastName.trim(),

        email:
          email.trim(),

        password,

        phone:
          phone.trim() ||
          undefined,
      },
      {
        onSuccess: () => {
          navigate(
            "/login",
            {
              replace: true,

              state: {
                registered: true,
              },
            },
          );
        },
      },
    );
  }


  return (
    <AuthLayout
      title="Rejoindre KBR"
      subtitle="Créez votre compte membre KBR."
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
              Prénom
            </label>

            <input
              id="firstName"
              type="text"
              autoComplete="given-name"
              required
              minLength={1}
              maxLength={100}
              value={firstName}
              onChange={(event) =>
                setFirstName(
                  event.target.value,
                )
              }
              className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
            />
          </div>


          <div>
            <label
              htmlFor="lastName"
              className="mb-2 block text-sm font-medium text-slate-200"
            >
              Nom
            </label>

            <input
              id="lastName"
              type="text"
              autoComplete="family-name"
              required
              minLength={1}
              maxLength={100}
              value={lastName}
              onChange={(event) =>
                setLastName(
                  event.target.value,
                )
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
            Adresse e-mail
          </label>

          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value,
              )
            }
            placeholder="vous@exemple.com"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>


        <div>
          <label
            htmlFor="phone"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Téléphone{" "}

            <span className="text-slate-500">
              (facultatif)
            </span>
          </label>

          <input
            id="phone"
            type="tel"
            autoComplete="tel"
            maxLength={30}
            value={phone}
            onChange={(event) =>
              setPhone(
                event.target.value,
              )
            }
            placeholder="+216 ..."
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>


        <div>
          <label
            htmlFor="password"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Mot de passe
          </label>

          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value,
              )
            }
            placeholder="Au moins 8 caractères"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
          />
        </div>


        <div>
          <label
            htmlFor="confirmPassword"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            Confirmer le mot de passe
          </label>

          <input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={confirmPassword}
            onChange={(event) =>
              setConfirmPassword(
                event.target.value,
              )
            }
            placeholder="Répétez votre mot de passe"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#f5c400]/60 focus:ring-2 focus:ring-[#f5c400]/10"
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
          Les nouveaux comptes doivent être
          activés avant de pouvoir se connecter.
        </div>


        <button
          type="submit"
          disabled={
            registerMutation.isPending
          }
          className="w-full rounded-xl bg-[#f5c400] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#ffd426] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {registerMutation.isPending
            ? "Création du compte..."
            : "Créer mon compte"}
        </button>
      </form>


      <div className="mt-6 border-t border-white/10 pt-6 text-center text-sm text-slate-400">
        Vous avez déjà un compte ?{" "}

        <Link
          to="/login"
          className="font-semibold text-[#f5c400] transition hover:text-[#ffd426]"
        >
          Se connecter
        </Link>
      </div>
    </AuthLayout>
  );
}