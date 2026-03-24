import { Link } from 'react-router-dom'
import { trustedBy } from '../data/siteContent'

export function HeroSection() {
  return (
    <section className="hero" id="hero">
      <div className="hero__background" aria-hidden="true" />
      <div className="hero__vignette" aria-hidden="true" />
      <div className="hero__focus" aria-hidden="true" />
      <div className="hero__glow" aria-hidden="true" />

      <div
        className="hero__content reveal is-visible"
        data-reveal
        style={{ ['--delay' as string]: '0ms' }}
      >
        <p className="eyebrow eyebrow--dark">FRAUDLENS</p>
        <h1>Clean the dataset before you trust the verdict.</h1>
        <p className="hero__subhead">
          A separate landing page, upload flow, and investigation workspace.
        </p>
        <p className="hero__body">
          FraudLens turns messy financial telemetry into an investigation-ready
          product journey. Start here, move into upload, then continue into a
          dedicated results environment built for deeper fraud analysis.
        </p>

        <div className="hero__actions">
          <Link to="/upload" className="button button--dark">
            Open upload page ↗
          </Link>
          <Link to="/results/demo" className="text-link">
            See the results workspace ↓
          </Link>
        </div>
      </div>

      <div
        className="trusted-bar reveal is-visible"
        data-reveal
        style={{ ['--delay' as string]: '160ms' }}
      >
        <p className="trusted-bar__label">TRUSTED BY FRAUD TEAMS AT</p>
        <div className="trusted-bar__logos" aria-label="Trusted by">
          {trustedBy.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </div>
    </section>
  )
}
