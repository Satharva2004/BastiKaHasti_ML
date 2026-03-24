import { ContourField } from '../components/ContourField'
import { SectionIntro } from '../components/SectionIntro'
import { signalCells, tickerItems } from '../data/siteContent'

export function SignalsSection() {
  return (
    <section className="section section--signals" id="use-cases">
      <ContourField className="contour contour--full" drift={2.2} />

      <div className="section__inner section__inner--wide">
        <SectionIntro eyebrow="THE INTELLIGENCE" title="Seven signals. One verdict." />

        <div
          className="ticker reveal"
          data-reveal
          style={{ ['--delay' as string]: '120ms' }}
        >
          <div className="ticker__track">
            {Array.from({ length: 2 }).map((_, trackIndex) => (
              <span key={trackIndex}>
                {tickerItems.map((item) => (
                  <span key={`${trackIndex}-${item}`}>{item}</span>
                ))}
              </span>
            ))}
          </div>
        </div>

        <div className="signal-grid">
          {signalCells.map((cell, index) => (
            <article
              key={cell.signal}
              className={`signal-card reveal ${
                index === signalCells.length - 1 ? 'signal-card--wide' : ''
              }`}
              data-reveal
              style={{ ['--delay' as string]: `${index * 70 + 180}ms` }}
            >
              <p className="signal-card__signal">{cell.signal}</p>
              <h3>{cell.headline}</h3>
              <p>{cell.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
