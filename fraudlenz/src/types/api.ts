export type DistributionMap = Record<string, number>

export type PreviewRow = Record<string, string | number | null>

export type TimestampRange = {
  min: string
  max: string
}

export type QualityMetrics = {
  unknown_device_count: number
  unknown_payment_method_count: number
  unknown_merchant_category_count: number
  invalid_ip_count: number
  zero_amount_count: number
  missing_city_count: number
  quality_score: number
  quality_level: string
}

export type DistributionPayload = {
  status: DistributionMap
  payment_method: DistributionMap
  merchant_category: DistributionMap
  canonical_city: DistributionMap
  merchant_canonical_city: DistributionMap
  device_type: DistributionMap
}

export type DatasetSummary = {
  row_count: number
  column_count: number
  duplicate_row_count: number
  missing_value_count: number
  missing_by_column: Record<string, number>
  numeric_columns: string[]
  categorical_columns: string[]
  top_cities: DistributionMap
  top_merchant_cities: DistributionMap
  top_device_types: DistributionMap
  amount_summary: {
    min: number
    max: number
    mean: number
    median: number
    p95: number
    p99: number
  }
}

export type ConfusionMatrix = {
  true_negative: number
  false_positive: number
  false_negative: number
  true_positive: number
}

export type ModelMetrics = {
  accuracy: number
  precision: number
  recall: number
  f1: number
  roc_auc: number
}

export type ThresholdRow = {
  threshold: number
  predicted_fraud: number
  precision: number
  recall: number
  f1: number
}

export type FeatureImportanceRow = {
  feature_name: string
  importance_score: number
}

export type RiskyTransaction = Record<string, string | number | null>

export type ModelArtifact = {
  model_name: 'random_forest' | 'xgboost' | string
  model_path: string
  metrics: ModelMetrics
  confusion_matrix: ConfusionMatrix
  fraud_detected_full_dataset: number
  predicted_non_fraud_full_dataset: number
  fraud_rate_full_dataset: number
  predictions_csv: string
  threshold_report_csv: string
  predictions_download_url: string
  threshold_report_download_url: string
  threshold_table: ThresholdRow[]
  feature_importance: FeatureImportanceRow[]
  top_risky_transactions: RiskyTransaction[]
  timing: Record<string, number>
}

export type PredictResponse = {
  file_id: string
  filename: string
  cleaned_filename: string
  cleaned_download_url: string
  dataset_summary: DatasetSummary
  row_count: number
  column_count: number
  columns: string[]
  target_column: string
  label_mode: string
  timing: Record<string, number>
  quality_metrics: QualityMetrics
  cleaning_actions: Record<string, string>
  distributions: DistributionPayload
  pattern_summary: Record<string, number>
  top_risky_transactions: RiskyTransaction[]
  timestamp_range: TimestampRange
  preview: PreviewRow[]
  models: ModelArtifact[]
}
