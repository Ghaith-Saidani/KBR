import {
  useNavigate,
  useParams,
} from "react-router-dom";

import ActivityForm from "../components/forms/ActivityForm";

import {
  useActivity,
  useUpdateActivity,
} from "../features/activities/activities.hooks";


export default function AdminActivityEditPage() {
  const navigate =
    useNavigate();

  const { id } =
    useParams<{
      id: string;
    }>();

  const {
    data: activity,
    isLoading,
    isError,
  } = useActivity(id);

  const mutation =
    useUpdateActivity();


  if (isLoading) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505]">
        <p className="text-sm text-slate-400">
          Chargement de l'activité...
        </p>
      </section>
    );
  }


  if (isError || !activity) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="text-center">

          <h1 className="text-2xl font-black">
            Activité introuvable
          </h1>

          <button
            type="button"
            onClick={() =>
              navigate(
                "/admin/activities",
              )
            }
            className="mt-5 rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-black text-black transition hover:bg-[#ffd21a]"
          >
            Retour aux activités
          </button>

        </div>
      </section>
    );
  }


  const activityId =
    activity.id;


  function handleSubmit(
    data: Parameters<
      React.ComponentProps<
        typeof ActivityForm
      >["onSubmit"]
    >[0],
  ) {
    mutation.mutate(
      {
        activityId,
        data,
      },
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
            Modifier l'activité
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Modifiez les informations de «{" "}
            {activity.title}
            {" "}».
          </p>

        </div>


        {mutation.isError && (
          <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
            Impossible de modifier
            l'activité. Vérifiez les
            informations saisies et
            réessayez.
          </div>
        )}


        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <ActivityForm
            activity={activity}
            submitLabel="Enregistrer les modifications"
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