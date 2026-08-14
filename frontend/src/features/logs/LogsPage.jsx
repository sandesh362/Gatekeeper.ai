export default function LogsPage() {
  return (
    <PlaceholderPage
      title="Logs"
      description="Audit trail of proxied LLM requests and detection outcomes."
    />
  )
}

function PlaceholderPage({ title, description }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-slate-400">{description}</p>
      </div>
      <div className="rounded-xl border border-dashed border-slate-700 p-12 text-center text-slate-500">
        Coming in Phase 2
      </div>
    </div>
  )
}
