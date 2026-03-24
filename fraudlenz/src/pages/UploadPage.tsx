import { useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SectionIntro } from '../components/SectionIntro'
import { SectionShell } from '../components/SectionShell'
import type { PredictResponse } from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'https://bastikahasti-ml.onrender.com'

async function analyzeCsv(file: File): Promise<PredictResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/predict-csv`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Upload failed.')
  }

  return (await response.json()) as PredictResponse
}

function resolveDownloadUrl(downloadUrl: string) {
  if (downloadUrl.startsWith('http://') || downloadUrl.startsWith('https://')) {
    return downloadUrl
  }

  return `${API_BASE_URL}${downloadUrl}`
}

export function UploadPage() {
  const inputId = useId()
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<PredictResponse | null>(null)

  async function handleUpload() {
    if (!selectedFile) {
      setError('Choose a CSV file before uploading.')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const response = await analyzeCsv(selectedFile)
      sessionStorage.setItem('fraudlens:last-result', JSON.stringify(response))
      setLastResult(response)
      navigate(`/results/${response.file_id}`, { state: { result: response } })
    } catch (uploadError) {
      const message =
        uploadError instanceof Error ? uploadError.message : 'Upload failed.'
      setError(message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <SectionShell
      id="upload"
      className="section--workbench page-section page-section--app"
      innerClassName="section__inner--wide"
      contourClassName="contour--subtle"
      contourDrift={1.1}
    >
      <div className="workbench-layout">
        <div className="workbench-layout__intro">
          <SectionIntro
            eyebrow="UPLOAD WORKSPACE"
            title="Turn a raw CSV into a fraud intelligence command center."
            copy="Upload a transaction file and the backend will clean it, engineer signals, score it with Random Forest and XGBoost, and return everything your frontend needs for charts, drill-downs, and model diagnostics."
          />
        </div>

        <div className="upload-card reveal is-visible" data-reveal>
          <p className="upload-card__label">POST /api/v1/predict-csv</p>
          <h3>Run full analysis</h3>
          <p className="upload-card__copy">
            The response includes the cleaned dataset, quality score, full
            distributions, pattern counts, model metrics, confusion matrices,
            feature importance, threshold tables, and high-risk transactions.
          </p>

          <label className="file-dropzone" htmlFor={inputId}>
            <input
              id={inputId}
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
            <span>{selectedFile ? selectedFile.name : 'Choose a CSV file'}</span>
            <small>
              {selectedFile
                ? `${(selectedFile.size / 1024).toFixed(1)} KB ready for analysis`
                : 'Drag a file here or browse from your machine'}
            </small>
          </label>

          <div className="upload-card__actions">
            <button
              type="button"
              className="button button--dark"
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading ? 'Analyzing in progress...' : 'Analyze and continue'}
            </button>
            <button
              type="button"
              className="button button--ghost button--ghost-dark"
              onClick={() => fileInputRef.current?.click()}
            >
              Pick another file
            </button>
          </div>

          {error ? <p className="form-message form-message--error">{error}</p> : null}
          {lastResult ? (
            <a
              className="download-link"
              href={resolveDownloadUrl(lastResult.cleaned_download_url)}
              target="_blank"
              rel="noreferrer"
            >
              Download latest cleaned CSV
            </a>
          ) : null}
        </div>
      </div>
    </SectionShell>
  )
}
