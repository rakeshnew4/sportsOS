import { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Sport gradient classes (e.g. "from-teal-600 to-cyan-500") drawn as a left accent bar. */
  accentGradient?: string;
  interactive?: boolean;
}

export function Card({ accentGradient, interactive, className = "", children, ...props }: CardProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-border bg-surface shadow-sm ${
        interactive ? "transition-shadow hover:shadow-lg" : ""
      } ${accentGradient ? "pl-5" : "p-4"} ${className}`}
      {...props}
    >
      {accentGradient && (
        <span className={`absolute inset-y-0 left-0 w-1.5 bg-gradient-to-b ${accentGradient}`} />
      )}
      <div className={accentGradient ? "py-4 pr-4" : ""}>{children}</div>
    </div>
  );
}
