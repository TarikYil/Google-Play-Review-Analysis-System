# Google Play Review Analysis System

A microservices-based system that collects Google Play Store reviews, runs sentiment analysis (positive/neutral/negative), detects fake reviews, discovers interesting reviews, visualizes the results, and exports them as CSV/JSON.

In short: collect → preprocess → analyze → visualize → export.

<img width="1909" height="906" alt="Ekran görüntüsü 2025-09-08 143540" src="https://github.com/user-attachments/assets/41b2471b-fe22-4515-9174-2cccc162ac13" />

## Features

- Data collection from Google Play Store
- Sentiment analysis (Transformer-based)
- Fake review detection (bot/spam/duplicate/synthetic)
- Interesting review discovery (humor/creativity/constructive)
- Export (CSV/JSON)
- Streamlit demo UI

## Architecture (simplified)

Three services:

1. Core Analysis Service (Port: 8000) — scraping, preprocessing, sentiment, fake detection, interesting detection
2. Export Service (Port: 8001) — CSV/JSON export & file management
3. Demo UI Service (Port: 8501) — Streamlit UI

## Getting Started

### Quick start (Docker)

```bash
docker-compose up --build
# UI:     http://localhost:8501
# Core:   http://localhost:8000
# Export: http://localhost:8001
```

Run in background:

```bash
docker-compose up -d --build
```

### Manual (without Docker)

```bash
# Core
cd service_core_analysis
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Export
cd service_exporter
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# UI
cd service_demo_ui
pip install -r requirements.txt
streamlit run app.py
```

## How to use

1. Open UI at http://localhost:8501
2. Enter a Google Play app ID (e.g., com.whatsapp) and set parameters
3. Click “Start Analysis”
4. Explore dashboards: Sentiment, Fake Reviews, Interesting Reviews
5. Export results as CSV/JSON

## 🔧 API Endpoints

- Core Analysis: http://localhost:8000/docs
- Export Service: http://localhost:8001/docs
- Demo UI: http://localhost:8501

### Example API calls

```bash
# Start analysis
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "com.whatsapp",
    "country": "tr",
    "language": "tr",
    "count": 1000
  }'

# Get results
curl "http://localhost:8000/api/v1/analyze/{job_id}"

# CSV export
curl -X POST "http://localhost:8001/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "{job_id}",
    "format": "csv"
  }'
```

## Data Flow

```
Google Play → Raw Reviews → Cleaned → Analyzed → Aggregated → Exported
```

## Tech Stack

- Backend (Core/Export): FastAPI (Python 3.11), Uvicorn
- ML/AI: Transformers (sentiment), scikit-learn, langdetect, TextBlob, sentence-transformers
- Scraping: google-play-scraper
- UI: Streamlit, Plotly, Pandas
- Data: JSON, CSV
- Containerization: Docker, Docker Compose

## Project Structure

```
Google Play Review Analysis System/
├── service_core_analysis/          # Core analysis service
│   ├── modules/
│   │   ├── data_collector.py       # Google Play scraper
│   │   ├── preprocessor.py         # Preprocessing
│   │   ├── sentiment_analyzer.py   # Sentiment
│   │   ├── fake_detector.py        # Fake detection
│   │   └── interesting_detector.py # Interesting detection
│   ├── routes/                     # API routes
│   ├── helpers/                    # Helpers
│   └── main.py                     # FastAPI app
├── service_exporter/               # Export service
├── service_demo_ui/                # Streamlit UI (app.py)
├── shared_data/                    # Runtime (mounted)
├── exports/                        # Runtime (mounted)
├── docker-compose.yml              # Docker configuration
└── README.md
```

## Analysis Details

### Sentiment Analysis
- Model: cardiffnlp/twitter-xlm-roberta-base-sentiment (multilingual)
- Classes: Positive, Neutral, Negative
- Fallback: TextBlob

### Fake Review Detection
- Pattern matching, anomaly detection, duplicate detection, user-behavior heuristics

### Interesting Review Detection
- Humor/creativity/constructive feedback signals, engagement heuristics

## Requirements

- Docker & Docker Compose (recommended)
- Python 3.11+ (for manual runs)
- 8GB+ RAM (for ML models)
- Internet connection (for scraping and first-time model downloads)
#


