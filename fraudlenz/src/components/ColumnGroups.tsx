type ColumnGroupsProps = {
  columns: string[]
}

const GROUPS: Array<{ title: string; columns: string[] }> = [
  {
    title: 'Core cleaned fields',
    columns: [
      'transaction_id',
      'user_id',
      'device_id',
      'device_type',
      'payment_method',
      'merchant_category',
      'status',
      'timestamp',
      'standardized_timestamp',
      'user_location',
      'merchant_location',
      'canonical_city',
      'merchant_canonical_city',
      'transaction_amount',
      'amt',
      'clean_amount',
      'account_balance',
      'ip_address',
    ],
  },
  {
    title: 'Behavioral features',
    columns: [
      'user_avg_spend',
      'spend_deviation',
      'is_new_device',
      'txn_count_1min',
      'txn_count_1h',
      'time_diff',
      'prev_status',
      'consecutive_failures',
      'device_user_degree',
      'ip_velocity_all_users',
    ],
  },
  {
    title: 'Risk signals',
    columns: [
      'is_micro_transaction',
      'failed_to_success_ratio_1h',
      'payment_method_entropy_10m',
      'balance_depletion_ratio',
      'post_txn_balance_danger',
      'is_cross_city',
      'hour',
      'is_odd_hour',
      'anomaly_score',
    ],
  },
  {
    title: 'Pattern outputs',
    columns: [
      'pattern_velocity',
      'pattern_device',
      'pattern_amount',
      'pattern_micro',
      'pattern_failure_burst',
      'pattern_time_gap',
      'fraud_label',
    ],
  },
]

export function ColumnGroups({ columns }: ColumnGroupsProps) {
  return (
    <div className="column-group-grid">
      {GROUPS.map((group) => {
        const availableColumns = group.columns.filter((column) => columns.includes(column))

        if (!availableColumns.length) {
          return null
        }

        return (
          <article key={group.title} className="result-panel reveal is-visible" data-reveal>
            <div className="result-panel__header">
              <p className="eyebrow">COLUMN FAMILY</p>
              <h3>{group.title}</h3>
            </div>
            <div className="chip-list">
              {availableColumns.map((column) => (
                <span key={column} className="chip">
                  {column}
                </span>
              ))}
            </div>
          </article>
        )
      })}
    </div>
  )
}
