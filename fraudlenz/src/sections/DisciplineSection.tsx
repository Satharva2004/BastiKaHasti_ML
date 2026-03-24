import { ContourField } from '../components/ContourField'
import { SectionIntro } from '../components/SectionIntro'
import { ledgerRows } from '../data/siteContent'

export function DisciplineSection() {
  return (
    <section className="section section--discipline" id="pricing">
      <ContourField className="contour contour--subtle" drift={0.8} />

      <div className="section__inner section__inner--wide">
        <SectionIntro
          eyebrow="THE DISCIPLINE"
          title="We don't clean data quietly."
          copy="Most fraud systems hide their data problems. FraudLens surfaces them. Every parsing decision, every city normalisation, every duplicate flagged - documented, quantified, and visible."
        />

        <div
          className="ledger reveal"
          data-reveal
          style={{ ['--delay' as string]: '120ms' }}
        >
          <div className="ledger__header">
            <p>WHAT WE FOUND</p>
            <p>WHAT WE DID</p>
          </div>

          {ledgerRows.map((row, index) => (
            <div
              key={row.found}
              className="ledger__row reveal"
              data-reveal
              style={{ ['--delay' as string]: `${index * 70 + 180}ms` }}
            >
              <p>{row.found}</p>
              <p>{row.did}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
