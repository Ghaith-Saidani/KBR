import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export default function AuthLayout({
  title,
  subtitle,
  children,
}: AuthLayoutProps) {
  return (
    <div className="relative min-h-[calc(100vh-160px)] overflow-hidden bg-[#050505]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(245,196,0,0.14),transparent_45%)]" />

      <div className="relative mx-auto flex min-h-[calc(100vh-160px)] w-full max-w-md items-center px-6 py-16">
        <div className="w-full">
          <div className="mb-8 text-center">
            <Link
              to="/"
              className="mb-8 inline-block text-2xl font-black tracking-[0.25em] text-[#f5c400]"
            >
              KBR
            </Link>

            <h1 className="text-3xl font-bold text-white">
              {title}
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              {subtitle}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 shadow-2xl backdrop-blur-xl sm:p-8">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}