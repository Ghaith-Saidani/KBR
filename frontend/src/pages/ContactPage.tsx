import {
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import {
  useSubmitContactMessage,
} from "../features/contact/contact.hooks";


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
    "Une erreur est survenue. Veuillez réessayer."
  );
}


const inputClassName =
  "w-full rounded-xl border border-white/10 bg-[#0B0B0B] px-4 py-3.5 text-sm text-white outline-none transition placeholder:text-white/25 focus:border-[#F5C400]/60 focus:ring-2 focus:ring-[#F5C400]/10";


export default function ContactPage() {
  const contactMutation =
    useSubmitContactMessage();

  const [
    name,
    setName,
  ] = useState("");

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    subject,
    setSubject,
  ] = useState("");

  const [
    message,
    setMessage,
  ] = useState("");


  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    contactMutation.mutate(
      {
        name: name.trim(),
        email: email.trim(),
        subject: subject.trim(),
        message: message.trim(),
      },
      {
        onSuccess: () => {
          setName("");
          setEmail("");
          setSubject("");
          setMessage("");
        },
      },
    );
  }


  return (
    <div className="bg-[#050505] text-white">

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_75%_35%,rgba(245,196,0,0.14),transparent_32%)]" />

        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8 lg:py-36">
          <div className="max-w-4xl">
            <p className="text-sm font-bold uppercase tracking-[0.3em] text-[#F5C400]">
              Contact
            </p>

            <h1 className="mt-5 text-5xl font-black uppercase leading-[0.92] tracking-tight sm:text-7xl lg:text-8xl">
              Parlons
              <span className="block text-[#F5C400]">
                ensemble.
              </span>
            </h1>

            <p className="mt-8 max-w-2xl text-lg leading-8 text-white/60 sm:text-xl">
              Une question, une proposition, un projet ou simplement
              envie d'échanger avec KBR ? Envoyez-nous un message.
            </p>
          </div>
        </div>
      </section>


      {/* Contact content */}
      <section className="bg-[#0A0A0A] py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">

          <div className="grid gap-14 lg:grid-cols-[0.7fr_1.3fr]">

            {/* Information */}
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
                Restons connectés
              </p>

              <h2 className="mt-4 text-4xl font-black uppercase tracking-tight sm:text-5xl">
                KBR est
                <span className="block text-[#F5C400]">
                  à votre écoute.
                </span>
              </h2>

              <p className="mt-6 max-w-md leading-8 text-white/50">
                Que vous soyez joueur, partenaire, organisateur,
                membre de la communauté ou simplement passionné
                d'eSports, nous sommes toujours ouverts aux échanges.
              </p>

              <div className="mt-12 space-y-6">

                <div className="border-l-2 border-[#F5C400] pl-5">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/30">
                    Localisation
                  </p>

                  <p className="mt-2 font-semibold text-white">
                    Bizerte, Tunisie
                  </p>
                </div>

                <div className="border-l-2 border-white/10 pl-5">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/30">
                    Réponse
                  </p>

                  <p className="mt-2 font-semibold text-white">
                    Nous vous répondrons dans les meilleurs délais.
                  </p>
                </div>

              </div>
            </div>


            {/* Form */}
            <div className="rounded-2xl border border-white/10 bg-[#050505] p-6 sm:p-8 lg:p-10">

              {contactMutation.isSuccess ? (
                <div className="flex min-h-[500px] flex-col items-center justify-center text-center">

                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#F5C400]/10 text-[#F5C400]">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      className="h-8 w-8"
                      aria-hidden="true"
                    >
                      <path
                        d="M5 12.5 9.5 17 19 7"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>

                  <h2 className="mt-6 text-3xl font-black uppercase">
                    Message envoyé.
                  </h2>

                  <p className="mt-4 max-w-md leading-7 text-white/50">
                    Merci pour votre message. L'équipe KBR a bien
                    reçu votre demande et reviendra vers vous
                    prochainement.
                  </p>

                  <button
                    type="button"
                    onClick={() =>
                      contactMutation.reset()
                    }
                    className="mt-8 rounded-lg bg-[#F5C400] px-6 py-3 text-sm font-bold text-[#050505] transition hover:bg-[#FFD21A]"
                  >
                    Envoyer un autre message
                  </button>
                </div>
              ) : (
                <>
                  <div className="mb-8">
                    <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F5C400]">
                      Écrivez-nous
                    </p>

                    <h2 className="mt-3 text-3xl font-black uppercase">
                      Votre message
                    </h2>

                    <p className="mt-3 text-sm leading-6 text-white/40">
                      Les champs marqués d'un astérisque sont
                      obligatoires.
                    </p>
                  </div>


                  <form
                    onSubmit={handleSubmit}
                    className="space-y-5"
                  >

                    {/* Name */}
                    <div>
                      <label
                        htmlFor="contact-name"
                        className="mb-2 block text-sm font-semibold text-white/80"
                      >
                        Nom complet *
                      </label>

                      <input
                        id="contact-name"
                        type="text"
                        required
                        minLength={2}
                        maxLength={150}
                        autoComplete="name"
                        value={name}
                        onChange={(event) =>
                          setName(
                            event.target.value,
                          )
                        }
                        placeholder="Votre nom"
                        className={inputClassName}
                      />
                    </div>


                    {/* Email */}
                    <div>
                      <label
                        htmlFor="contact-email"
                        className="mb-2 block text-sm font-semibold text-white/80"
                      >
                        Adresse e-mail *
                      </label>

                      <input
                        id="contact-email"
                        type="email"
                        required
                        autoComplete="email"
                        value={email}
                        onChange={(event) =>
                          setEmail(
                            event.target.value,
                          )
                        }
                        placeholder="vous@exemple.com"
                        className={inputClassName}
                      />
                    </div>


                    {/* Subject */}
                    <div>
                      <label
                        htmlFor="contact-subject"
                        className="mb-2 block text-sm font-semibold text-white/80"
                      >
                        Sujet *
                      </label>

                      <input
                        id="contact-subject"
                        type="text"
                        required
                        minLength={3}
                        maxLength={200}
                        value={subject}
                        onChange={(event) =>
                          setSubject(
                            event.target.value,
                          )
                        }
                        placeholder="Comment pouvons-nous vous aider ?"
                        className={inputClassName}
                      />
                    </div>


                    {/* Message */}
                    <div>
                      <label
                        htmlFor="contact-message"
                        className="mb-2 block text-sm font-semibold text-white/80"
                      >
                        Message *
                      </label>

                      <textarea
                        id="contact-message"
                        required
                        minLength={10}
                        maxLength={10_000}
                        rows={7}
                        value={message}
                        onChange={(event) =>
                          setMessage(
                            event.target.value,
                          )
                        }
                        placeholder="Écrivez votre message..."
                        className={`${inputClassName} resize-y`}
                      />

                      <div className="mt-2 text-right text-xs text-white/25">
                        {message.length} / 10 000
                      </div>
                    </div>


                    {/* Error */}
                    {contactMutation.isError && (
                      <div
                        role="alert"
                        className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm leading-6 text-red-300"
                      >
                        {getErrorMessage(
                          contactMutation.error,
                        )}
                      </div>
                    )}


                    {/* Submit */}
                    <button
                      type="submit"
                      disabled={
                        contactMutation.isPending
                      }
                      className="w-full rounded-xl bg-[#F5C400] px-5 py-4 text-sm font-black uppercase tracking-wide text-[#050505] transition hover:bg-[#FFD21A] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {contactMutation.isPending
                        ? "Envoi en cours..."
                        : "Envoyer le message"}
                    </button>

                  </form>
                </>
              )}

            </div>

          </div>
        </div>
      </section>


      {/* Bottom CTA */}
      <section className="border-t border-white/10 bg-[#050505] py-20">
        <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">

          <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
            Knights of Bizertin Rise
          </p>

          <h2 className="mx-auto mt-4 max-w-3xl text-3xl font-black uppercase tracking-tight sm:text-5xl">
            Built in Bizerte.
            <span className="block text-[#F5C400]">
              Driven by competition.
            </span>
          </h2>

        </div>
      </section>

    </div>
  );
}