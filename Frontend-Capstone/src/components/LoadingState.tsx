type LoadingStateProps = {
  message?: string;
};

export default function LoadingState({
  message = "Loading, please wait...",
}: LoadingStateProps) {
  // front end ui
  return (
    <div className="glass-panel flex min-h-[320px] flex-col items-center justify-center gap-4 rounded-[2rem] p-8 text-center">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-100 border-t-cyan-700" />
      <p className="max-w-md text-sm leading-6 text-slate-600">{message}</p>
    </div>
  );
}
