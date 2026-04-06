export default function Loading() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-10 w-64 rounded bg-mist" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="h-56 rounded-3xl bg-mist" />
        <div className="h-56 rounded-3xl bg-mist" />
        <div className="h-56 rounded-3xl bg-mist" />
      </div>
    </div>
  );
}
