import { Link } from "react-router-dom";
import KBRLogo from "../../assets/KBR_Logo.jpg";

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
      <img
        src={KBRLogo}
        alt=""
        aria-hidden="true"
        className="h-11 w-11 shrink-0 rounded-xl bg-white object-contain p-0.5"
      />

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
