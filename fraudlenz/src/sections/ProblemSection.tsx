import { SectionIntro } from '../components/SectionIntro'
import { ContourField } from '../components/ContourField'
import { stats } from '../data/siteContent'

export function ProblemSection() {
  return (
    <section className="section section--problem" id="product">
      <ContourField className="contour contour--bottom" drift={0.35} />

      <div className="section__inner">
        <SectionIntro
          eyebrow="THE PROBLEM"
          title="Fraud doesn't announce itself."
          copy="Every day, thousands of transactions slip through outdated rule-based systems. By the time your team reviews the alert, the money is gone. FraudLens doesn't wait for rules. It learns your users - and flags the moment something doesn't fit."
        />

        <div
          className="stat-frame reveal"
          data-reveal
          style={{ ['--delay' as string]: '120ms' }}
        >
          <div className="stat-frame__line" />
          <div className="stats-row">
            {stats.map((stat, index) => (
              <div
                key={stat.value}
                className="stat reveal"
                data-reveal
                style={{ ['--delay' as string]: `${index * 80 + 180}ms` }}
              >
                <div className="stat__value">{stat.value}</div>
                <div className="stat__label">{stat.label}</div>
              </div>
            ))}
          </div>
          <div className="stat-frame__line" />
        </div>
      </div>
    </section>
  )
}
