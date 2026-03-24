import { Link, useLocation, useParams } from 'react-router-dom'
import { ResultsWorkspace } from '../components/ResultsWorkspace'
import { SectionShell } from '../components/SectionShell'
import type { PredictResponse } from '../types/api'

type ResultsLocationState = {
  result?: PredictResponse
}

function getStoredResult() {
  const stored = sessionStorage.getItem('fraudlens:last-result')
  if (!stored) {
    return null
  }

  try {
    return JSON.parse(stored) as PredictResponse
  } catch {
    return null
  }
}

export function ResultsPage() {
  const { fileId } = useParams()
  const location = useLocation()
  const state = location.state as ResultsLocationState | null
  const result = state?.result ?? getStoredResult()

  return (
    <SectionShell
      id="results"
      className="section--workbench page-section page-section--app"
      innerClassName="section__inner--wide"
      contourClassName="contour--subtle"
      contourDrift={1.4}
    >
      <div className="workspace-header reveal is-visible" data-reveal>
        <div>
          <p className="eyebrow">RESULTS WORKSPACE</p>
          <h2>Fraud intelligence control room</h2>
          <p className="section-copy">
            File ID: {fileId ?? 'unknown'} . Explore the cleaned dataset, compact data
            quality, interactive pattern distributions, model evidence, and user-level
            transaction drilldown from one modular workspace.
          </p>
        </div>
        <div className="workspace-header__actions">
          <Link to="/upload" className="button button--ghost">
            Upload another file
          </Link>
        </div>
      </div>

      {result ? (
        <ResultsWorkspace result={result} />
      ) : (
        <div className="empty-state reveal is-visible" data-reveal>
          <p className="eyebrow">NO RESULT LOADED</p>
          <h3>There is no uploaded dataset attached to this workspace yet.</h3>
          <p>
            Start on the upload page, run the full prediction API, and return here
            with the generated file ID.
          </p>
          <Link to="/upload" className="button button--outline">
            Go to upload page
          </Link>
        </div>
      )}
    </SectionShell>
  )
}
