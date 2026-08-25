import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="text-center">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-slate-400">
          404
        </p>

        <h1 className="mt-3 text-4xl font-black text-slate-950">
          Page introuvable
        </h1>

        <p className="mx-auto mt-4 max-w-md text-slate-600">
          La page que vous recherchez n'existe pas ou a été déplacée.
        </p>

        <Link
          to="/"
          className="mt-8 inline-flex rounded-xl bg-slate-950 px-6 py-3 text-sm font-bold text-white transition hover:bg-slate-800"
        >
          Retour à l'accueil
        </Link>
      </div>
    </section>
  );
}