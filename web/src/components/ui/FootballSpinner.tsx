export function FootballSpinner({
  label,
  className = "",
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center gap-2 py-6 ${className}`}>
      <span className="inline-block animate-spin text-3xl motion-reduce:animate-none">⚽</span>
      {label && <p className="text-sm text-ink-muted">{label}</p>}
    </div>
  );
}
