type QualityMetricsProps = {
  metrics: Record<string, number>
}

function formatMetricLabel(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export function QualityMetrics({ metrics }: QualityMetricsProps) {
  return (
    <div className="metric-grid">
      {Object.entries(metrics).map(([key, value], index) => (
        <article
          key={key}
          className="metric-card reveal is-visible"
          data-reveal
          style={{ ['--delay' as string]: `${index * 70}ms` }}
        >
          <p className="metric-card__label">{formatMetricLabel(key)}</p>
          <strong>{value.toLocaleString()}</strong>
        </article>
      ))}
    </div>
  )
}
