import { Link } from 'react-router-dom'
import { HeroSection } from '../sections/HeroSection'

export function HomePage() {
  return (
    <>
      <HeroSection />
      <section className="landing-bridge">
        <div className="landing-bridge__inner reveal is-visible" data-reveal>
          <p className="eyebrow">NEXT STEP</p>
          <h2>Move from brand story to live dataset review.</h2>
          <p className="section-copy">
            The landing page stays focused. Upload and analysis now live in their own
            product workspace so the investigation flow feels deliberate.
          </p>
          <div className="landing-bridge__actions">
            <Link to="/upload" className="button button--outline">
              Open upload workspace ↗
            </Link>
            <Link to="/results/demo" className="button button--ghost">
              See results shell →
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
