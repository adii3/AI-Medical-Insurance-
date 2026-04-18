type ErrorStateProps = {
  title?: string;
  message?: string;
  onRetry?: () => void;
};

export default function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load your data. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="glass-panel flex min-h-[320px] flex-col items-center justify-center gap-4 rounded-[2rem] p-8 text-center">
      <div className="rounded-full bg-rose-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-rose-700">
        Attention Needed
      </div>
      <h2 className="text-xl font-semibold text-slate-950">{title}</h2>
      <p className="max-w-md text-sm leading-6 text-slate-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-full bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
        >
          Try again
        </button>
      )}
    </div>
  );
}
