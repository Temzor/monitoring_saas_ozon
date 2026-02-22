# monitoring_saas_ozon

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Python API     │────▶│   PostgreSQL    │
│   (HTML/JS)     │◀────│   (FastAPI)      │◀────│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Go Checker    │◀────│   Redis Queue    │────▶│   Email Alerts │
│   (Goroutines)  │────▶│                  │     │   (Celery)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘


Structur:
uptime-monitor/
├── api/                    # Python FastAPI
│   ├── main.py
│   ├── models.py
│   ├── auth.py
│   └── requirements.txt
├── checker/                # Go checker service
│   ├── main.go
│   ├── checker.go
│   ├── go.mod
│   └── go.sum
├── worker/                 # Python Celery worker for emails
│   ├── tasks.py
│   └── requirements.txt
├── frontend/               # Simple HTML/JS
│   ├── index.html
│   └── app.js
├── docker-compose.yml
└── .env
