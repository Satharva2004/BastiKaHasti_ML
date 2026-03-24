import { ContourField } from '../components/ContourField'
import { SectionIntro } from '../components/SectionIntro'

export function CtaSection() {
  return (
    <section className="section section--cta" id="cta">
      <ContourField className="contour contour--cta" drift={2.9} height={820} />

      <div className="section__inner">
        <SectionIntro
          eyebrow="FRAUDLENS · EARLY ACCESS"
          title="The best fraud detection system is built by the team that understood the data the deepest."
          copy="Request access to the FraudLens pipeline. Built for fraud operations teams who need reasoning, not just alerts."
          className="cta-intro"
        />

        <div
          className="cta-actions reveal"
          data-reveal
          style={{ ['--delay' as string]: '120ms' }}
        >
          <a href="mailto:hello@fraudlens.ai" className="button button--outline">
            Request early access ↗
          </a>
          <a href="#how-it-works" className="button button--ghost">
            View the pipeline docs →
          </a>
        </div>
      </div>
    </section>
  )
}
