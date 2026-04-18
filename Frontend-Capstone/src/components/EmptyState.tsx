type EmptyStateProps = {
  title?: string;
  message?: string;
};

export default function EmptyState({
  title = "No data available",
  message = "There's nothing to display right now.",
}: EmptyStateProps) {
  return (
    <div className="glass-panel flex min-h-[320px] flex-col items-center justify-center gap-4 rounded-[2rem] p-8 text-center">
      <div className="rounded-full bg-amber-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-amber-700">
        Waiting For Data
      </div>
      <h2 className="text-xl font-semibold text-slate-950">{title}</h2>
      <p className="max-w-md text-sm leading-6 text-slate-600">{message}</p>
    </div>
  );
}
