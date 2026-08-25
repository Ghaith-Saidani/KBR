import { Link } from "react-router-dom";

interface LogoProps {
  showName?: boolean;
  dark?: boolean;
}

export default function Logo({
  showName = true,
  dark = false,
}: LogoProps) {
  return (
    <Link
      to="/"
      className="group flex items-center gap-3"
      aria-label="Knights of Bizertin Rise"
    >
      <div className="relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-[#F5C400]">
        <span className="text-sm font-black tracking-tighter text-[#0A0A0A]">
          KBR
        </span>

        <span className="absolute bottom-0 left-0 h-1 w-full bg-[#0A0A0A]" />
      </div>

      {showName && (
        <div className="hidden sm:block">
          <p
            className={[
              "text-sm font-black tracking-tight",
              dark ? "text-white" : "text-[#0A0A0A]",
            ].join(" ")}
          >
            Knights of Bizertin Rise
          </p>

          <p
            className={[
              "text-xs",
              dark ? "text-white/50" : "text-[#666666]",
            ].join(" ")}
          >
            Ensemble pour avancer
          </p>
        </div>
      )}
    </Link>
  );
}