export const navItems = ['Upload', 'Results', 'Preview']

export const trustedBy = [
  'HDFC BANK',
  'RAZORPAY',
  'PAYTM',
  'ZEPTO',
  'CRED',
  'PHONEPE',
  'ZOMATO',
  'GROWW',
]

export const stats = [
  { value: '$485B', label: 'lost to fraud annually' },
  { value: '3.2%', label: 'average false positive rate' },
  { value: '47min', label: 'mean detection lag' },
]

export const pipelineStages = [
  {
    number: '01',
    name: 'DATA INGESTION',
    description:
      '100K+ transactions. 15 columns. 6 amount formats, 7 timestamp formats, messy real-world inputs.',
  },
  {
    number: '02',
    name: 'CLEANING + NORMALISATION',
    description:
      'City variants clustered via fuzzy matching. Timestamps unified. Duplicate records quantified, not dropped.',
  },
  {
    number: '03',
    name: 'FEATURE ENGINEERING',
    description:
      "Per-user DNA: avg spend, home city, typical hour, preferred device. Every transaction scored against the user's own baseline.",
  },
  {
    number: '04',
    name: 'FRAUD DETECTION',
    description:
      'LightGBM trained on behavioural features. Class-balanced. Reports precision, recall, and F1 - never just accuracy.',
  },
  {
    number: '05',
    name: 'EXPLAINABILITY',
    description:
      'SHAP TreeExplainer. Every flagged transaction returns a structured audit trail: which signals fired, deviation magnitudes, confidence score.',
  },
]

export const signalCells = [
  {
    signal: 'GEO DEVIATION',
    headline: 'Mumbai at 9am. Delhi at 3am.',
    description:
      "User's home city profiled from 847 prior transactions. A location never visited in 2 years triggers an immediate flag.",
  },
  {
    signal: 'NEW DEVICE',
    headline: 'Same card. Different machine.',
    description:
      'Every device_id logged per user. First-time web session from a mobile-only user: flagged, logged, explained.',
  },
  {
    signal: 'VELOCITY SPIKE',
    headline: '2 transactions a week. 19 in 7 days.',
    description:
      'Rolling 7-day velocity tracked per user. A 9.5x spike in transaction frequency is a signal, not noise.',
  },
  {
    signal: 'AMOUNT ANOMALY',
    headline: 'Rs1,200 average. Rs47,000 today.',
    description:
      "Every transaction z-scored against the user's own spend distribution - not a global threshold. 4.2 sigma above mean: flagged.",
  },
  {
    signal: 'HOUR OUTLIER',
    headline: 'Always 9am-1pm. Today: 3:14am.',
    description:
      'Temporal profile built per user. Transactions outside the 2 sigma hour window are combined with other signals.',
  },
  {
    signal: 'CATEGORY JUMP',
    headline: '847 transactions. Zero electronics. Until today.',
    description:
      'Category history tracked for every user. First-time category purchase at elevated amount: anomaly score elevated.',
  },
  {
    signal: 'IP MISMATCH',
    headline: 'Known subnet. Suddenly: 0.0.0.0.',
    description:
      'IP address validated structurally and against user history. Malformed, private, or first-seen IP blocks compound the fraud score.',
  },
]

export const tickerItems = [
  'GEO DEVIATION',
  'NEW DEVICE',
  'VELOCITY SPIKE',
  'AMOUNT ANOMALY',
  'HOUR OUTLIER',
  'CATEGORY JUMP',
  'IP MISMATCH',
]

export const ledgerRows = [
  {
    found: '6 distinct amount formats in a single column',
    did: 'Regex parser handles Rs3,200, 3200 INR, Rs 3200, 3200.0, 3200.0000, and null before analysis.',
  },
  {
    found: '7 distinct timestamp formats',
    did: "Unix epoch, ISO 8601, compact, and human-readable formats parsed. Failures marked as 'parse_fail', never silently zeroed.",
  },
  {
    found: 'Mumbai, MUMBAI, BOM, Bombay, mUMBAI, MUM',
    did: 'Fuzzy string clustering with RapidFuzz plus DBSCAN builds the normalisation map from the data itself.',
  },
  {
    found: '1,204 exact duplicate rows + 389 same-ID-different-value rows',
    did: 'Two deduplication passes preserve both classes with a dup_type column rather than dropping them.',
  },
  {
    found: '107 invalid IP addresses including 0.0.0.0 and 192.168..1',
    did: 'Structural validation via regex plus the ipaddress module adds ip_valid=false directly into the feature set.',
  },
  {
    found: '33 zero-amount transactions',
    did: 'Preserved as fraud signal candidates rather than removed. zero_amount becomes a model-ready feature.',
  },
]
