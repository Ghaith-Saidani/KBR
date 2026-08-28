import {
  useNavigate,
} from "react-router-dom";

import ActivityForm from "../components/forms/ActivityForm";

import {
  useCreateActivity,
} from "../features/activities/activities.hooks";


export default function AdminActivityCreatePage() {
  const navigate =
    useNavigate();

  const mutation =
    useCreateActivity();


  function handleSubmit(
    data: Parameters<
      React.ComponentProps<
        typeof ActivityForm
      >["onSubmit"]
    >[0],
  ) {
    mutation.mutate(
      data,
      {
        onSuccess: () => {
          navigate(
            "/admin/activities",
          );
        },
      },
    );
  }


  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl">

        <div className="mb-8">
          <button
            type="button"
            onClick={() =>
              navigate(
                "/admin/activities",
              )
            }
            className="text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
          >
            ← Retour aux activités
          </button>

          <p className="mt-8 text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <h1 className="mt-2 text-3xl font-black sm:text-4xl">
            Nouvelle activité
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Créez une nouvelle activité
            pour la communauté KBR.
          </p>
        </div>


        {mutation.isError && (
          <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
            Impossible de créer
            l'activité. Vérifiez les
            informations saisies et
            réessayez.
          </div>
        )}


        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <ActivityForm
            submitLabel="Créer l'activité"
            isSubmitting={
              mutation.isPending
            }
            onSubmit={
              handleSubmit
            }
          />
        </div>

      </div>
    </section>
  );
}