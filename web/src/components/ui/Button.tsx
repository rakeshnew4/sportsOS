"use client";

import { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "gradient" | "danger";

const variantClasses: Record<Variant, string> = {
  primary: "bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-emerald-300",
  secondary:
    "bg-surface text-foreground border border-border hover:bg-surface-muted disabled:opacity-50",
  ghost: "bg-transparent text-ink-muted hover:bg-surface-muted disabled:opacity-50",
  gradient:
    "bg-gradient-to-r from-brand-from to-brand-to text-white shadow-md shadow-indigo-600/20 hover:brightness-110 disabled:opacity-50 disabled:brightness-100",
  danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
};

export function Button({
  variant = "primary",
  pill = false,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; pill?: boolean }) {
  return (
    <button
      className={`px-4 py-2.5 ${pill ? "rounded-full" : "rounded-xl"} font-semibold text-sm transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:active:scale-100 ${variantClasses[variant]} ${className}`}
      {...props}
    />
  );
}
