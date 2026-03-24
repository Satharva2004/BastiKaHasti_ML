# BastiKaHasti ML

Fraud detection workspace with a FastAPI backend for CSV cleaning, feature engineering, fraud-pattern analysis, and model scoring, plus a React frontend for interactive visualization.

## Live Deployment

- Backend API: [https://bastikahasti-ml.onrender.com/](https://bastikahasti-ml.onrender.com/)
- API Docs: [https://bastikahasti-ml.onrender.com/docs](https://bastikahasti-ml.onrender.com/docs)

## What This Project Does

- Uploads raw transaction CSV files
- Cleans inconsistent values like amounts, timestamps, cities, device values, and statuses
- Generates fraud-focused engineered features
- Applies business fraud patterns such as:
  - location mismatch
  - odd-hour transaction
  - high amount vs balance
  - unknown device
  - failed high-value attempt
  - IP risk
  - velocity
  - post-failure success
- Trains and scores `XGBoost` and `Random Forest`
- Returns frontend-ready analytics for dashboards, charts, drilldowns, and downloads

## Project Structure

```text
BastiKaHasti_ML/
├─ server/       FastAPI backend, pipeline, model training, storage
└─ fraudlenz/    React + Vite frontend
```

## Key Backend Endpoints

### `GET /health`

Simple health check.

### `POST /api/v1/clean-csv`

Uploads a raw CSV, runs the cleaning pipeline, saves the cleaned CSV, and returns:

- row and column counts
- preview rows
- quality metrics
- cleaning actions
- distribution summaries
- pattern summaries
- cleaned file download URL

### `POST /api/v1/predict-csv`

Uploads a raw CSV, runs the cleaning pipeline, then trains and scores the models. Returns:

- dataset summary
- quality score and quality level
- city, payment method, merchant category, merchant city, device type, and status distributions
- pattern summary
- top risky transactions
- model metrics
- confusion matrix
- threshold table
- feature importance
- artifact download URLs

### Download Routes

- `GET /api/v1/clean-csv/{file_id}/download`
- `GET /api/v1/predict-csv/{file_id}/download/cleaned`
- `GET /api/v1/predict-csv/{file_id}/download/{model_name}/predictions`
- `GET /api/v1/predict-csv/{file_id}/download/{model_name}/thresholds`

## Backend Setup

```bash
cd server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.server:app --reload
```

Backend will run on:

```text
http://127.0.0.1:8000
```

## Frontend Setup

```bash
cd fraudlenz
npm install
npm run dev
```

Optional frontend environment variable:

```text
VITE_API_BASE_URL=https://bastikahasti-ml.onrender.com
```

If not set, the frontend falls back to the hosted backend URL above.

## Example API Usage

### Clean a CSV

Windows `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/clean-csv" ^
  -F "file=@C:\path\to\sample.csv"
```

### Run Full Prediction Pipeline

Windows `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict-csv" ^
  -F "file=@C:\path\to\sample.csv"
```

## Data Cleaning Highlights

The pipeline currently standardizes or derives:

- transaction amount
- timestamps
- canonical user and merchant cities
- device and status normalization
- invalid IP handling
- per-user and per-device behavior signals
- amount-to-balance ratio
- odd-hour flags
- cross-city flags
- fraud pattern columns

It also returns cleaning explanations so the frontend can show what was done to messy data.

## Model Outputs

Each prediction run can return:

- predicted fraud and non-fraud counts
- fraud probability scores
- confusion matrix
- precision, recall, F1, ROC-AUC
- threshold sweeps
- feature importance
- transaction-level prediction CSVs

## Notes

- Some datasets may use a proxy `fraud_label` when confirmed fraud ground truth is not available.
- Render is used for backend deployment because the Python ML stack is too heavy for a small Vercel serverless bundle.
- The frontend is designed to support drilldowns by model, transaction, feature, and fraud pattern.

## Tech Stack

### Backend

- Python
- FastAPI
- pandas
- numpy
- scikit-learn
- XGBoost
- joblib

### Frontend

- React
- TypeScript
- Vite
- React Router
