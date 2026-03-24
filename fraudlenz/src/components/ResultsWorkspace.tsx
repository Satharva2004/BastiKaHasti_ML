import { useMemo, useState } from 'react'
import { resolveDownloadUrl } from '../lib/api'
import type {
  DistributionMap,
  ModelArtifact,
  PredictResponse,
  RiskyTransaction,
} from '../types/api'

type ResultsWorkspaceProps = {
  result: PredictResponse
}

const paymentMethodDisplay: Record<string, string> = {
  upi: 'UPI',
  card: 'Card',
  wallet: 'Wallet',
  netbanking: 'Net Banking',
  unknown_payment_method: 'Unknown',
}

const paymentMethodIcon: Record<string, string> = {
  upi: 'UP',
  card: 'CR',
  wallet: 'WL',
  netbanking: 'NB',
  unknown_payment_method: '??',
}

function formatLabel(value: string) {
  return value
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

function DistributionCard({
  title,
  items,
  variant = 'default',
}: {
  title: string
  items: DistributionMap
  variant?: 'default' | 'payment'
}) {
  const entries = Object.entries(items) as Array<[string, number]>
  entries.sort((a, b) => b[1] - a[1])
  const maxValue = Math.max(...entries.map(([, value]) => value), 1)

  return (
    <article className="distribution-card reveal is-visible" data-reveal>
      <header className="distribution-card__header">
        <p className="eyebrow">DISTRIBUTION</p>
        <h3>{title}</h3>
      </header>

      <div className="distribution-list distribution-list--tall">
        {entries.map(([label, value], index) => (
          <div
            key={label}
            className={`distribution-row${variant === 'payment' ? ' distribution-row--payment' : ''}`}
            style={{ ['--delay' as string]: `${index * 35}ms` }}
          >
            <div className="distribution-row__meta">
              <span className="distribution-row__label">
                {variant === 'payment' ? (
                  <span className="payment-pill">
                    <span className="payment-pill__icon">
                      {paymentMethodIcon[label] ?? label.slice(0, 2).toUpperCase()}
                    </span>
                    <span>{paymentMethodDisplay[label] ?? formatLabel(label)}</span>
                  </span>
                ) : (
                  formatLabel(label)
                )}
              </span>
              <strong>{formatNumber(value)}</strong>
            </div>
            <div className="distribution-row__track">
              <div
                className="distribution-row__fill"
                style={{ width: `${(value / maxValue) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

function QualityPanel({
  qualityMetrics,
  cleaningActions,
}: {
  qualityMetrics: PredictResponse['quality_metrics']
  cleaningActions: PredictResponse['cleaning_actions']
}) {
  const qualityLevelClass = `quality-badge quality-badge--${qualityMetrics.quality_level}`
  const issueCards = Object.entries(qualityMetrics).filter(
    ([key]) => !['quality_score', 'quality_level'].includes(key),
  )

  return (
    <div className="result-panel reveal is-visible" data-reveal>
      <div className="result-panel__header result-panel__header--spread">
        <div>
          <p className="eyebrow">DATA QUALITY</p>
          <h3>How healthy is this upload?</h3>
        </div>
        <div className="quality-summary">
          <span className={qualityLevelClass}>{qualityMetrics.quality_level}</span>
          <strong>{qualityMetrics.quality_score}/100</strong>
        </div>
      </div>

      <div className="metric-grid metric-grid--quality">
        {issueCards.map(([key, value], index) => (
          <article
            key={key}
            className="metric-card reveal is-visible"
            data-reveal
            style={{ ['--delay' as string]: `${index * 55}ms` }}
          >
            <p className="metric-card__label">{formatLabel(key)}</p>
            <strong>{formatNumber(Number(value))}</strong>
          </article>
        ))}
      </div>

      <div className="action-grid">
        {Object.entries(cleaningActions).map(([key, value]) => (
          <article key={key} className="action-card">
            <p className="metric-card__label">{formatLabel(key)}</p>
            <p>{String(value)}</p>
          </article>
        ))}
      </div>
    </div>
  )
}

function PatternPanel({
  patternSummary,
}: {
  patternSummary: PredictResponse['pattern_summary']
}) {
  const patternEntries = Object.entries(patternSummary) as Array<[string, number]>
  return (
    <div className="result-panel reveal is-visible" data-reveal>
      <div className="result-panel__header">
        <p className="eyebrow">PATTERN ENGINE</p>
        <h3>What the rule system is seeing</h3>
      </div>
      <div className="metric-grid metric-grid--patterns">
        {patternEntries
          .sort((a, b) => b[1] - a[1])
          .map(([pattern, count], index) => (
            <article
              key={pattern}
              className="metric-card reveal is-visible"
              data-reveal
              style={{ ['--delay' as string]: `${index * 55}ms` }}
            >
              <p className="metric-card__label">{formatLabel(pattern)}</p>
              <strong>{formatNumber(Number(count))}</strong>
            </article>
          ))}
      </div>
    </div>
  )
}

function ModelPanel({ model }: { model: ModelArtifact }) {
  return (
    <article className="result-panel reveal is-visible" data-reveal>
      <div className="result-panel__header result-panel__header--spread">
        <div>
          <p className="eyebrow">MODEL LAB</p>
          <h3>{formatLabel(model.model_name)}</h3>
        </div>
        <div className="model-downloads">
          <a
            className="button button--ghost button--small"
            href={resolveDownloadUrl(model.predictions_download_url)}
            target="_blank"
            rel="noreferrer"
          >
            Predictions CSV
          </a>
          <a
            className="button button--ghost button--small"
            href={resolveDownloadUrl(model.threshold_report_download_url)}
            target="_blank"
            rel="noreferrer"
          >
            Thresholds CSV
          </a>
        </div>
      </div>

      <div className="result-grid result-grid--model">
        {[
          ['Accuracy', formatPercent(model.metrics.accuracy)],
          ['Precision', formatPercent(model.metrics.precision)],
          ['Recall', formatPercent(model.metrics.recall)],
          ['F1 Score', formatPercent(model.metrics.f1)],
          ['ROC AUC', formatPercent(model.metrics.roc_auc)],
          ['Fraud detected', formatNumber(model.fraud_detected_full_dataset)],
        ].map(([label, value]) => (
          <article key={label} className="result-card">
            <p className="result-card__label">{label}</p>
            <h3>{value}</h3>
          </article>
        ))}
      </div>

      <div className="matrix-grid">
        {Object.entries(model.confusion_matrix).map(([label, value]) => (
          <article key={label} className="matrix-card">
            <p className="metric-card__label">{formatLabel(label)}</p>
            <strong>{formatNumber(value)}</strong>
          </article>
        ))}
      </div>

      <div className="dual-panel-grid">
        <div className="mini-table-card">
          <header className="mini-table-card__header">
            <p className="eyebrow">THRESHOLDS</p>
            <h4>Precision and recall by cutoff</h4>
          </header>
          <div className="mini-table-wrap">
            <table className="mini-table">
              <thead>
                <tr>
                  <th>Threshold</th>
                  <th>Fraud</th>
                  <th>Precision</th>
                  <th>Recall</th>
                </tr>
              </thead>
              <tbody>
                {model.threshold_table.map((row) => (
                  <tr key={row.threshold}>
                    <td>{row.threshold.toFixed(1)}</td>
                    <td>{formatNumber(row.predicted_fraud)}</td>
                    <td>{formatPercent(row.precision)}</td>
                    <td>{formatPercent(row.recall)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mini-table-card">
          <header className="mini-table-card__header">
            <p className="eyebrow">FEATURE IMPORTANCE</p>
            <h4>Top contributors</h4>
          </header>
          <div className="distribution-list">
            {model.feature_importance.slice(0, 8).map((item) => (
              <div key={item.feature_name} className="distribution-row">
                <div className="distribution-row__meta">
                  <span>{item.feature_name.replace(/^numeric__|^categorical__/, '')}</span>
                  <strong>{item.importance_score.toFixed(3)}</strong>
                </div>
                <div className="distribution-row__track">
                  <div
                    className="distribution-row__fill"
                    style={{
                      width: `${(item.importance_score / (model.feature_importance[0]?.importance_score || 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </article>
  )
}

function TransactionExplorer({
  transactions,
}: {
  transactions: RiskyTransaction[]
}) {
  const patternOptions = useMemo(() => {
    const keys = new Set<string>()
    transactions.forEach((transaction) => {
      Object.keys(transaction).forEach((key) => {
        if (key.startsWith('pattern_')) {
          keys.add(key)
        }
      })
    })
    return ['all', ...Array.from(keys)]
  }, [transactions])

  const [selectedPattern, setSelectedPattern] = useState('all')
  const [selectedTransaction, setSelectedTransaction] = useState<RiskyTransaction | null>(
    transactions[0] ?? null,
  )

  const filteredTransactions = useMemo(() => {
    if (selectedPattern === 'all') {
      return transactions
    }

    return transactions.filter((transaction) => Number(transaction[selectedPattern] ?? 0) === 1)
  }, [selectedPattern, transactions])

  return (
    <div className="result-panel reveal is-visible" data-reveal>
      <div className="result-panel__header result-panel__header--spread">
        <div>
          <p className="eyebrow">TRANSACTION EXPLORER</p>
          <h3>Click into risky transactions and pattern clusters</h3>
        </div>
        <div className="chip-list">
          {patternOptions.map((pattern) => (
            <button
              key={pattern}
              type="button"
              className={`chip chip--interactive${selectedPattern === pattern ? ' chip--active' : ''}`}
              onClick={() => setSelectedPattern(pattern)}
            >
              {pattern === 'all' ? 'All patterns' : formatLabel(pattern)}
            </button>
          ))}
        </div>
      </div>

      <div className="explorer-grid">
        <div className="explorer-list">
          {filteredTransactions.map((transaction) => (
            <button
              key={`${transaction.transaction_id}-${transaction.fraud_probability}`}
              type="button"
              className={`transaction-tile${selectedTransaction === transaction ? ' transaction-tile--active' : ''}`}
              onClick={() => setSelectedTransaction(transaction)}
            >
              <div>
                <p className="metric-card__label">{String(transaction.transaction_id ?? 'Unknown transaction')}</p>
                <strong>{formatNumber(Number(transaction.clean_amount ?? 0), 2)}</strong>
              </div>
              <span>{formatPercent(Number(transaction.fraud_probability ?? 0))}</span>
            </button>
          ))}
        </div>

        <div className="transaction-detail">
          {selectedTransaction ? (
            <>
              <div className="transaction-detail__hero">
                <p className="eyebrow">SELECTED TRANSACTION</p>
                <h3>{String(selectedTransaction.transaction_id ?? 'Unknown')}</h3>
                <p>
                  User {String(selectedTransaction.user_id ?? '-')} .
                  Probability {formatPercent(Number(selectedTransaction.fraud_probability ?? 0))}
                </p>
              </div>
              <div className="detail-grid">
                {Object.entries(selectedTransaction).map(([key, value]) => (
                  <div key={key} className="detail-row">
                    <span>{formatLabel(key)}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p>No transaction selected.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export function ResultsWorkspace({ result }: ResultsWorkspaceProps) {
  const preferredModel = result.models.find((model) => model.model_name === 'xgboost') ?? result.models[0]

  return (
    <div className="result-stack" id="results">
      <div className="result-header reveal is-visible" data-reveal>
        <p className="eyebrow">ANALYSIS RESPONSE</p>
        <h2>{result.filename}</h2>
        <p className="section-copy">
          Timestamp window: {result.timestamp_range.min} to {result.timestamp_range.max}
        </p>
      </div>

      <div className="result-grid result-grid--headline">
        {[
          ['Rows analyzed', formatNumber(result.row_count)],
          ['Columns available', formatNumber(result.column_count)],
          ['Target column', result.target_column],
          ['Quality score', `${result.quality_metrics.quality_score}/100`],
          ['Fraud detected', formatNumber(preferredModel.fraud_detected_full_dataset)],
          ['File ID', result.file_id],
        ].map(([label, value]) => (
          <article key={label} className="result-card reveal is-visible" data-reveal>
            <p className="result-card__label">{label}</p>
            <h3>{value}</h3>
          </article>
        ))}
      </div>

      <QualityPanel qualityMetrics={result.quality_metrics} cleaningActions={result.cleaning_actions} />

      <PatternPanel patternSummary={result.pattern_summary} />

      <div className="distribution-grid distribution-grid--wide">
        <DistributionCard title="City Distribution" items={result.distributions.canonical_city} />
        <DistributionCard
          title="Merchant City Distribution"
          items={result.distributions.merchant_canonical_city}
        />
        <DistributionCard
          title="Payment Method Mix"
          items={result.distributions.payment_method}
          variant="payment"
        />
        <DistributionCard title="Merchant Categories" items={result.distributions.merchant_category} />
      </div>

      <div className="result-panel reveal is-visible" data-reveal>
        <div className="result-panel__header result-panel__header--spread">
          <div>
            <p className="eyebrow">DATASET SNAPSHOT</p>
            <h3>Quick file summary for the clean CSV</h3>
          </div>
          <a
            className="button button--ghost button--small"
            href={resolveDownloadUrl(result.cleaned_download_url)}
            target="_blank"
            rel="noreferrer"
          >
            Download cleaned CSV
          </a>
        </div>

        <div className="result-grid result-grid--dataset">
          <article className="result-card">
            <p className="result-card__label">Duplicate rows</p>
            <h3>{formatNumber(result.dataset_summary.duplicate_row_count)}</h3>
          </article>
          <article className="result-card">
            <p className="result-card__label">Missing values</p>
            <h3>{formatNumber(result.dataset_summary.missing_value_count)}</h3>
          </article>
          <article className="result-card">
            <p className="result-card__label">P95 amount</p>
            <h3>{formatNumber(result.dataset_summary.amount_summary.p95, 2)}</h3>
          </article>
          <article className="result-card">
            <p className="result-card__label">P99 amount</p>
            <h3>{formatNumber(result.dataset_summary.amount_summary.p99, 2)}</h3>
          </article>
        </div>

        <div className="chip-list">
          {result.columns.map((column) => (
            <span key={column} className="chip">
              {column}
            </span>
          ))}
        </div>
      </div>

      <div className="model-grid">
        {result.models.map((model) => (
          <ModelPanel key={model.model_name} model={model} />
        ))}
      </div>

      <TransactionExplorer transactions={preferredModel.top_risky_transactions} />
    </div>
  )
}
