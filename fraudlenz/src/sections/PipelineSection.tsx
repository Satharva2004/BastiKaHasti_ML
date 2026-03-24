import { ContourField } from '../components/ContourField'
import { SectionIntro } from '../components/SectionIntro'
import { pipelineStages } from '../data/siteContent'

export function PipelineSection() {
  return (
    <section className="section section--pipeline" id="how-it-works">
      <ContourField className="contour contour--right" drift={1.3} />

      <div className="section__inner section__inner--wide">
        <SectionIntro eyebrow="THE PIPELINE" title="From raw noise to clear signal." />

        <div className="pipeline-grid">
          {pipelineStages.map((stage, index) => (
            <article
              key={stage.number}
              className="pipeline-card reveal"
              data-reveal
              style={{ ['--delay' as string]: `${index * 80 + 120}ms` }}
            >
              <p className="pipeline-card__number">{stage.number}</p>
              <h3>{stage.name}</h3>
              <p>{stage.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
