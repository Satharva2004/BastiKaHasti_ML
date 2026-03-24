import { useEffect, useMemo, useState } from 'react'
import type { ModelArtifact, PredictResponse, RiskyTransaction } from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'https://bastikahasti-ml.onrender.com'

function resolveDownloadUrl(downloadUrl: string) {
  if (downloadUrl.startsWith('http://') || downloadUrl.startsWith('https://')) {
    return downloadUrl
  }
  return `${API_BASE_URL}${downloadUrl}`
}

function formatLabel(value: string) {
  return value
    .replace(/^pattern_/, '')
    .replace(/^numeric__|^categorical__/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatNumber(value: number, digits = 0) {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function getModelComplexity(modelName: string) {
  return modelName === 'xgboost'
    ? {
        training: 'O(T · N · D)',
        prediction: 'O(T · D)',
        note: 'Boosting rounds × rows × tree depth',
      }
    : {
        training: 'O(T · N · log N)',
        prediction: 'O(T · D)',
        note: 'Trees × rows × split search',
      }
}

function paymentVisual(method: string) {
  const value = method.toLowerCase()
  if (value === 'upi') {
    return 'https://commons.wikimedia.org/wiki/Special:Redirect/file/UPI%20logo.svg'
  }
  if (value === 'card') {
    return 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Mastercard-logo.svg'
  }
  return null
}

function mergeTransactions(result: PredictResponse) {
  const seen = new Set<string>()
  const merged: RiskyTransaction[] = []
  ;[result.top_risky_transactions, ...result.models.map((model) => model.top_risky_transactions)]
    .flat()
    .forEach((transaction) => {
      const key = `${String(transaction.transaction_id ?? 'unknown')}::${String(transaction.user_id ?? 'unknown')}`
      if (seen.has(key)) return
      seen.add(key)
      merged.push(transaction)
    })
  return merged
}

function SimpleDistribution({
  title,
  items,
  kind = 'default',
}: {
  title: string
  items: Record<string, number>
  kind?: 'default' | 'payment'
}) {
  const entries = Object.entries(items).sort((a, b) => b[1] - a[1]).slice(0, 6)
  const max = Math.max(...entries.map(([, count]) => count), 1)

  return (
    <article className="glass-panel section-panel">
      <div className="section-panel__header">
        <div>
          <p className="eyebrow eyebrow--dark">Distribution</p>
          <h3>{title}</h3>
        </div>
      </div>
      <div className="data-bars">
        {entries.map(([label, count]) => (
          <div key={label} className="data-bar">
            <div className="data-bar__meta">
              <div className="data-bar__identity">
                {kind === 'payment' ? (
                  paymentVisual(label) ? (
                    <span className="data-bar__icon">
                      <img className="brand-icon brand-icon--image" src={paymentVisual(label) ?? ''} alt={label} />
                    </span>
                  ) : (
                    <span className="data-bar__icon data-bar__icon--fallback">{label.slice(0, 2).toUpperCase()}</span>
                  )
                ) : null}
                <span>{formatLabel(label)}</span>
              </div>
              <strong>{formatNumber(count)}</strong>
            </div>
            <div className="data-bar__track">
              <div className="data-bar__fill" style={{ width: `${(count / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

function ModelPanel({ model }: { model: ModelArtifact }) {
  const complexity = getModelComplexity(model.model_name)

  return (
    <div className="tab-stack">
      <section className="glass-panel section-panel">
        <div className="section-panel__header section-panel__header--spread">
          <div>
            <p className="eyebrow eyebrow--dark">Model Lab</p>
            <h3>{formatLabel(model.model_name)}</h3>
          </div>
          <div className="download-row">
            <a className="button button--ghost-dark button--small" href={resolveDownloadUrl(model.predictions_download_url)} target="_blank" rel="noreferrer">
              Predictions CSV
            </a>
            <a className="button button--ghost-dark button--small" href={resolveDownloadUrl(model.threshold_report_download_url)} target="_blank" rel="noreferrer">
              Thresholds CSV
            </a>
          </div>
        </div>

        <div className="model-summary-grid">
          <article className="model-score-card model-score-card--fraud">
            <span>Fraud detected</span>
            <strong>{formatNumber(model.fraud_detected_full_dataset)}</strong>
            <small>{formatPercent(model.fraud_rate_full_dataset)} of all rows</small>
          </article>
          <article className="model-score-card model-score-card--safe">
            <span>Non-fraud detected</span>
            <strong>{formatNumber(model.predicted_non_fraud_full_dataset)}</strong>
            <small>Predicted safe by the model</small>
          </article>
          <article className="model-score-card">
            <span>Accuracy</span>
            <strong>{formatPercent(model.metrics.accuracy)}</strong>
            <small>Holdout benchmark</small>
          </article>
          <article className="model-score-card">
            <span>Precision</span>
            <strong>{formatPercent(model.metrics.precision)}</strong>
            <small>{formatPercent(model.metrics.recall)} recall</small>
          </article>
        </div>

        <div className="complexity-strip">
          <article className="complexity-card">
            <span>Training complexity</span>
            <strong>{complexity.training}</strong>
            <small>{complexity.note}</small>
          </article>
          <article className="complexity-card">
            <span>Prediction complexity</span>
            <strong>{complexity.prediction}</strong>
            <small>Each row traverses all trees during inference</small>
          </article>
        </div>

        <div className="matrix-and-chart">
          <div className="matrix-board">
            {Object.entries(model.confusion_matrix).map(([label, value]) => (
              <article key={label} className="matrix-board__cell">
                <span>{formatLabel(label)}</span>
                <strong>{formatNumber(value)}</strong>
              </article>
            ))}
          </div>

          <div className="threshold-board">
            <div className="timing-list">
              {Object.entries(model.timing).map(([key, value]) => (
                <div key={key} className="timing-list__row">
                  <span>{formatLabel(key)}</span>
                  <strong>{formatNumber(value, 2)} ms</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export function ResultsWorkspace({ result }: { result: PredictResponse }) {
  const [activeTab, setActiveTab] = useState<'overview' | 'patterns' | 'models' | 'transactions'>('overview')
  const [selectedModelName] = useState(
    result.models.find((model) => model.model_name === 'xgboost')?.model_name ?? result.models[0]?.model_name ?? '',
  )
  const selectedModel = result.models.find((model) => model.model_name === selectedModelName) ?? result.models[0]
  const transactions = useMemo(() => mergeTransactions(result), [result])
  const users = useMemo(() => {
    const grouped = new Map<string, { userId: string; total: number; maxRisk: number; totalAmount: number }>()
    transactions.forEach((transaction) => {
      const userId = String(transaction.user_id ?? 'unknown')
      const probability = Number(transaction.fraud_probability ?? 0)
      const amount = Number(transaction.clean_amount ?? 0)
      const current = grouped.get(userId) ?? { userId, total: 0, maxRisk: 0, totalAmount: 0 }
      current.total += 1
      current.maxRisk = Math.max(current.maxRisk, probability)
      current.totalAmount += amount
      grouped.set(userId, current)
    })
    return Array.from(grouped.values()).sort((a, b) => b.maxRisk - a.maxRisk)
  }, [transactions])

  const [selectedUser, setSelectedUser] = useState(users[0]?.userId ?? 'unknown')
  useEffect(() => {
    if (!users.find((user) => user.userId === selectedUser)) {
      setSelectedUser(users[0]?.userId ?? 'unknown')
    }
  }, [users, selectedUser])

  const userTransactions = useMemo(
    () =>
      transactions
        .filter((transaction) => String(transaction.user_id ?? 'unknown') === selectedUser)
        .sort((a, b) => Number(b.fraud_probability ?? 0) - Number(a.fraud_probability ?? 0)),
    [selectedUser, transactions],
  )
  const [selectedTransactionId, setSelectedTransactionId] = useState('')
  useEffect(() => {
    setSelectedTransactionId(String(userTransactions[0]?.transaction_id ?? ''))
  }, [selectedUser, userTransactions])

  const selectedTransaction =
    userTransactions.find((transaction) => String(transaction.transaction_id) === selectedTransactionId) ?? userTransactions[0]
  const [showAllDetails, setShowAllDetails] = useState(false)
  const detailEntries = selectedTransaction ? Object.entries(selectedTransaction) : []
  const visibleDetails = showAllDetails ? detailEntries : detailEntries.slice(0, 8)

  return (
    <div className="results-shell">
      <section className="results-hero">
        <div className="results-hero__copy">
          <p className="eyebrow eyebrow--dark">Fraud Intelligence Workspace</p>
          <h2>{result.filename}</h2>
          <p className="results-hero__lead">
            Cleaner layout, fewer but more meaningful metrics, and a user-first transaction view.
          </p>
          <div className="results-hero__actions">
            <a className="button button--dark" href={resolveDownloadUrl(result.cleaned_download_url)} target="_blank" rel="noreferrer">
              Download cleaned CSV
            </a>
            <div className="results-hero__meta">
              <span>{result.label_mode.toUpperCase()} labels</span>
              <span>{result.target_column}</span>
              <span>{result.timestamp_range.min} to {result.timestamp_range.max}</span>
            </div>
          </div>
        </div>

        <div className="hero-summary-grid">
          <article className="hero-kpi hero-kpi--primary">
            <p>Fraud predicted by {formatLabel(selectedModel.model_name)}</p>
            <strong>{formatNumber(selectedModel.fraud_detected_full_dataset)}</strong>
            <span>{formatPercent(selectedModel.fraud_rate_full_dataset)} of file</span>
          </article>
          <article className="hero-kpi">
            <p>Rows</p>
            <strong>{formatNumber(result.row_count)}</strong>
            <span>{formatNumber(result.column_count)} columns</span>
          </article>
          <article className="hero-kpi">
            <p>Precision</p>
            <strong>{formatPercent(selectedModel.metrics.precision)}</strong>
            <span>{formatPercent(selectedModel.metrics.recall)} recall</span>
          </article>
          <article className="hero-kpi">
            <p>Quality score</p>
            <strong>{result.quality_metrics.quality_score.toFixed(0)}</strong>
            <span>{result.quality_metrics.quality_level}</span>
          </article>
        </div>
      </section>

      <div className="workspace-switcher">
        {[
          ['overview', 'Overview'],
          ['patterns', 'Patterns'],
          ['models', 'Model Lab'],
          ['transactions', 'Transactions'],
        ].map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={`workspace-switcher__tab${activeTab === value ? ' workspace-switcher__tab--active' : ''}`}
            onClick={() => setActiveTab(value as 'overview' | 'patterns' | 'models' | 'transactions')}
          >
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' ? (
        <div className="results-layout">
          <div className="results-main">
            <section className="glass-panel section-panel">
              <div className="section-panel__header">
                <div>
                  <p className="eyebrow eyebrow--dark">File Snapshot</p>
                  <h3>Minimal summary, high-signal numbers</h3>
                </div>
              </div>
              <div className="compact-kpi-grid">
                <article className="compact-kpi">
                  <span>Missing values</span>
                  <strong>{formatNumber(result.dataset_summary.missing_value_count)}</strong>
                </article>
                <article className="compact-kpi">
                  <span>Duplicates</span>
                  <strong>{formatNumber(result.dataset_summary.duplicate_row_count)}</strong>
                </article>
                <article className="compact-kpi">
                  <span>Average amount</span>
                  <strong>{formatNumber(result.dataset_summary.amount_summary.mean, 2)}</strong>
                </article>
                <article className="compact-kpi">
                  <span>Pattern signals</span>
                  <strong>{formatNumber(Object.values(result.pattern_summary).reduce((sum, value) => sum + value, 0))}</strong>
                </article>
              </div>
              <div className="overview-spotlight">
                <SimpleDistribution title="Payment mix" items={result.distributions.payment_method} kind="payment" />
                <SimpleDistribution title="Top merchant categories" items={result.distributions.merchant_category} />
              </div>
            </section>

            <section className="glass-panel section-panel">
              <div className="section-panel__header section-panel__header--spread">
                <div>
                  <p className="eyebrow eyebrow--dark">Transaction Preview</p>
                  <h3>Recent cleaned transactions</h3>
                </div>
              </div>
              <div className="preview-sheet">
                <div className="preview-sheet__head">
                  <span>Transaction</span>
                  <span>User</span>
                  <span>Status</span>
                  <span>Amount</span>
                  <span>City</span>
                </div>
                {result.preview.slice(0, 6).map((row, index) => (
                  <div key={`${row.transaction_id ?? index}`} className="preview-sheet__row">
                    <span>{String(row.transaction_id ?? 'Unknown')}</span>
                    <span>{String(row.user_id ?? 'Unknown')}</span>
                    <span>{String(row.status ?? '-')}</span>
                    <span>{String(row.clean_amount ?? row.transaction_amount ?? '-')}</span>
                    <span>{String(row.canonical_city ?? row.user_location ?? '-')}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <aside className="results-sidebar">
            <section className="quality-rail glass-panel">
              <div className="quality-rail__header">
                <p className="eyebrow eyebrow--dark">Data Quality</p>
                <div className={`quality-rail__tone quality-rail__tone--${result.quality_metrics.quality_level}`}>
                  {result.quality_metrics.quality_level}
                </div>
              </div>
              <div className="quality-rail__score">
                <strong>{result.quality_metrics.quality_score.toFixed(0)}</strong>
                <span>/100</span>
              </div>
              <div className="quality-rail__metrics">
                {[
                  ['Invalid IPs', result.quality_metrics.invalid_ip_count],
                  ['Unknown devices', result.quality_metrics.unknown_device_count],
                  ['Zero amounts', result.quality_metrics.zero_amount_count],
                  ['Missing cities', result.quality_metrics.missing_city_count],
                ].map(([label, value]) => (
                  <div key={label} className="quality-rail__metric">
                    <span>{label}</span>
                    <strong>{formatNumber(Number(value))}</strong>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      ) : null}

      {activeTab === 'patterns' ? (
        <div className="analytics-grid">
          <SimpleDistribution title="Pattern counts" items={result.pattern_summary} />
          <SimpleDistribution title="All user cities" items={result.distributions.canonical_city} />
          <SimpleDistribution title="Merchant categories" items={result.distributions.merchant_category} />
        </div>
      ) : null}

      {activeTab === 'models' ? <ModelPanel model={selectedModel} /> : null}

      {activeTab === 'transactions' ? (
        <section className="glass-panel section-panel transaction-studio">
          <div className="section-panel__header">
            <div>
              <p className="eyebrow eyebrow--dark">Transaction Studio</p>
              <h3>Click a user, then inspect their transactions</h3>
            </div>
          </div>

          <div className="studio-grid">
            <div className="studio-rail">
              <h4 className="studio-column__title">Users</h4>
              <div className="user-list">
                {users.map((user) => (
                  <button
                    key={user.userId}
                    type="button"
                    className={`user-card${selectedUser === user.userId ? ' user-card--active' : ''}`}
                    onClick={() => setSelectedUser(user.userId)}
                  >
                    <strong>{user.userId}</strong>
                    <span>{user.total} transactions</span>
                    <small>Peak risk {formatPercent(user.maxRisk)}</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="studio-main">
              <div className="studio-user-summary">
                <p className="eyebrow eyebrow--dark">Selected User</p>
                <h4 className="studio-column__title">{selectedUser}</h4>
                <div className="studio-user-summary__metrics">
                  <span>{userTransactions.length} flagged transactions</span>
                  <span>{formatNumber(userTransactions.reduce((sum, item) => sum + Number(item.clean_amount ?? 0), 0), 2)} total amount</span>
                </div>
              </div>

              <div className="transaction-strip">
                <div className="transaction-strip__header">
                  <h4 className="studio-column__title">Transactions</h4>
                  <span>{userTransactions.length} rows</span>
                </div>
                <div className="transaction-list">
                  {userTransactions.map((transaction) => (
                    <button
                      key={String(transaction.transaction_id)}
                      type="button"
                      className={`transaction-card${String(transaction.transaction_id) === selectedTransactionId ? ' transaction-card--active' : ''}`}
                      onClick={() => setSelectedTransactionId(String(transaction.transaction_id))}
                    >
                      <div>
                        <strong>{String(transaction.transaction_id)}</strong>
                        <span>{formatNumber(Number(transaction.clean_amount ?? 0), 2)}</span>
                      </div>
                      <small>{formatPercent(Number(transaction.fraud_probability ?? 0))}</small>
                    </button>
                  ))}
                </div>
              </div>

              <div className="studio-detail glass-panel glass-panel--nested">
                {selectedTransaction ? (
                  <>
                    <div className="studio-detail__hero">
                      <p className="eyebrow eyebrow--dark">Selected Transaction</p>
                      <h3>{String(selectedTransaction.transaction_id)}</h3>
                      <p>
                        User {String(selectedTransaction.user_id)} . Fraud probability{' '}
                        {formatPercent(Number(selectedTransaction.fraud_probability ?? 0))}
                      </p>
                    </div>
                    <div className="detail-grid detail-grid--studio">
                      {visibleDetails.map(([key, value]) => (
                        <article key={key} className="detail-card">
                          <span>{formatLabel(key)}</span>
                          <strong>{String(value)}</strong>
                        </article>
                      ))}
                    </div>
                    {detailEntries.length > 8 ? (
                      <button type="button" className="button button--ghost-dark button--small" onClick={() => setShowAllDetails((value) => !value)}>
                        {showAllDetails ? 'Show less' : 'Show more'}
                      </button>
                    ) : null}
                  </>
                ) : null}
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  )
}
