import { ArrowRight, ChevronDown, Trophy } from "lucide-react";
import { Link } from "react-router-dom";

export default function HeroSection() {
  return (
    <section className="relative min-h-[calc(100vh-5rem)] overflow-hidden bg-[#050505]">
      {/* Background atmosphere */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-10%] top-[10%] h-[500px] w-[500px] rounded-full bg-[#F5C400]/5 blur-[120px]" />

        <div className="absolute right-[-5%] top-[15%] h-[650px] w-[650px] rounded-full bg-[#F5C400]/8 blur-[140px]" />

        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
          }}
        />

        <div className="absolute inset-y-0 left-1/2 hidden w-px bg-white/[0.04] lg:block" />
      </div>

      <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl items-center px-4 py-16 sm:px-6 sm:py-20 lg:px-8 lg:py-24">
        <div className="grid w-full items-center gap-16 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
          {/* Left side — main message */}
          <div className="relative z-10">
            {/* Eyebrow */}
            <div className="mb-7 inline-flex items-center gap-3 rounded-full border border-[#F5C400]/25 bg-[#F5C400]/[0.04] px-4 py-2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#F5C400] opacity-50" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#F5C400]" />
              </span>

              <span className="text-xs font-bold uppercase tracking-[0.22em] text-[#F5C400] sm:text-sm">
                Club eSports · Bizerte · Tunisie
              </span>
            </div>

            {/* Heading */}
            <h1 className="max-w-4xl text-[3.5rem] font-black uppercase leading-[0.88] tracking-[-0.045em] text-white sm:text-6xl md:text-7xl lg:text-[5.6rem] xl:text-[6.4rem]">
              Knights
              <span className="block text-white">of</span>
              <span className="block text-[#F5C400]">
                Bizertin Rise
              </span>
            </h1>

            {/* Description */}
            <p className="mt-8 max-w-2xl text-base leading-7 text-white/60 sm:text-lg sm:leading-8 lg:text-xl">
              Un club eSports basé à Bizerte, dédié à la compétition, au
              développement des talents et à la représentation de la Tunisie
              sur la scène nationale et internationale.
            </p>

            {/* CTAs */}
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/events"
                className="kbr-button-primary group gap-2"
              >
                Découvrir les événements

                <ArrowRight
                  size={18}
                  strokeWidth={2.5}
                  className="transition-transform duration-200 group-hover:translate-x-1"
                />
              </Link>

              <Link
                to="/about"
                className="kbr-button-secondary"
              >
                Découvrir KBR
              </Link>
            </div>

            {/* Identity facts */}
            <div className="mt-12 grid max-w-2xl grid-cols-1 border-t border-white/10 pt-6 sm:grid-cols-3">
              <div className="border-b border-white/10 pb-5 sm:border-b-0 sm:border-r sm:pb-0 sm:pr-6">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/35">
                  Base
                </p>

                <p className="mt-2 text-sm font-bold text-white sm:text-base">
                  Bizerte, Tunisie
                </p>
              </div>

              <div className="border-b border-white/10 py-5 sm:border-b-0 sm:border-r sm:px-6 sm:py-0">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/35">
                  Ambition
                </p>

                <p className="mt-2 text-sm font-bold text-white sm:text-base">
                  Tunisie & International
                </p>
              </div>

              <div className="pt-5 sm:px-6 sm:pt-0">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/35">
                  Univers
                </p>

                <p className="mt-2 text-sm font-bold text-[#F5C400] sm:text-base">
                  eSports
                </p>
              </div>
            </div>
          </div>

          {/* Right side — KBR visual identity */}
          <div className="relative hidden min-h-[560px] items-center justify-center lg:flex">
            {/* Outer decorative ring */}
            <div className="absolute h-[500px] w-[500px] rounded-full border border-white/[0.055]" />

            <div className="absolute h-[410px] w-[410px] rounded-full border border-[#F5C400]/10" />

            <div className="absolute h-[300px] w-[300px] rounded-full border border-white/[0.04]" />

            {/* Glow */}
            <div className="absolute h-[360px] w-[360px] rounded-full bg-[#F5C400]/10 blur-[90px]" />

            {/* Main KBR mark */}
            <div className="relative flex h-[360px] w-[360px] items-center justify-center rounded-full border border-[#F5C400]/20 bg-[#0b0b0b]/80 shadow-[0_0_100px_rgba(245,196,0,0.08)] backdrop-blur-sm">
              <div className="absolute inset-5 rounded-full border border-white/[0.06]" />

              <div className="text-center">
                <div className="text-[8rem] font-black leading-none tracking-[-0.1em] text-white">
                  K<span className="text-[#F5C400]">B</span>R
                </div>

                <div className="mt-2 flex items-center justify-center gap-3">
                  <span className="h-px w-8 bg-[#F5C400]/60" />

                  <span className="text-[10px] font-bold uppercase tracking-[0.35em] text-white/45">
                    Bizertin Rise
                  </span>

                  <span className="h-px w-8 bg-[#F5C400]/60" />
                </div>
              </div>
            </div>

            {/* Top floating card */}
            <div className="absolute right-0 top-12 rounded-xl border border-white/10 bg-[#0d0d0d]/90 px-4 py-3 shadow-2xl backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#F5C400] text-[#050505]">
                  <Trophy size={18} strokeWidth={2.5} />
                </div>

                <div>
                  <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-white/35">
                    Mission
                  </p>

                  <p className="mt-0.5 text-xs font-bold text-white">
                    Compétition
                  </p>
                </div>
              </div>
            </div>

            {/* Bottom floating card */}
            <div className="absolute bottom-14 left-0 rounded-xl border border-white/10 bg-[#0d0d0d]/90 px-5 py-4 shadow-2xl backdrop-blur-md">
              <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-white/35">
                Location
              </p>

              <div className="mt-1 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#F5C400]" />

                <p className="text-sm font-bold text-white">
                  Bizerte, Tunisia
                </p>
              </div>
            </div>

            {/* Decorative corner lines */}
            <div className="absolute right-10 top-1/2 h-16 w-16 -translate-y-1/2 border-r border-t border-[#F5C400]/30" />

            <div className="absolute bottom-24 left-16 h-12 w-12 border-b border-l border-[#F5C400]/20" />

            {/* Small orbit dots */}
            <span className="absolute left-[18%] top-[28%] h-1.5 w-1.5 rounded-full bg-[#F5C400]" />

            <span className="absolute right-[18%] bottom-[30%] h-1 w-1 rounded-full bg-white/40" />

            <span className="absolute right-[28%] top-[20%] h-1 w-1 rounded-full bg-[#F5C400]/60" />
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-6 left-1/2 hidden -translate-x-1/2 flex-col items-center gap-2 text-white/25 lg:flex">
        <span className="text-[9px] font-bold uppercase tracking-[0.25em]">
          Explorer
        </span>

        <ChevronDown
          size={16}
          className="animate-bounce"
        />
      </div>
    </section>
  );
}