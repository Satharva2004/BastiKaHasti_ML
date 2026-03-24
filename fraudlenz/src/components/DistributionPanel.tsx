import type { DistributionMap } from '../types/api'

type DistributionPanelProps = {
  title: string
  items: DistributionMap
}

export function DistributionPanel({ title, items }: DistributionPanelProps) {
  const entries = Object.entries(items)
  const maxValue = Math.max(...entries.map(([, value]) => value), 1)

  return (
    <article className="distribution-card reveal is-visible" data-reveal>
      <header className="distribution-card__header">
        <p className="eyebrow">DISTRIBUTION</p>
        <h3>{title}</h3>
      </header>

      <div className="distribution-list">
        {entries.map(([label, value], index) => (
          <div
            key={label}
            className="distribution-row"
            style={{ ['--delay' as string]: `${index * 50}ms` }}
          >
            <div className="distribution-row__meta">
              <span>{label}</span>
              <strong>{value.toLocaleString()}</strong>
            </div>
            <div className="distribution-row__track">
              <div
                className="distribution-row__fill"
                style={{ width: `${(value / maxValue) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}
