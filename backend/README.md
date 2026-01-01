# Opinion Builder Tools - Backend

FastAPI backend for discovering and filtering prediction market topics from opinion.trade.

## Features

- **Topic Discovery**: Fetch topics from opinion.trade API
- **Keyword Search**: Search topics by keywords
- **Advanced Filtering**: Filter by end date, outcome type, categories, price range, volume
- **Real-time Updates**: WebSocket integration for live price updates

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### Setup

```bash
# Install uv if you haven't already
pip install uv

# Install dependencies
cd backend
uv sync

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys
```

## Running the Server

```bash
# Start the development server
uv run uvicorn opinion_builder.main:app --reload

# Or specify host and port
uv run uvicorn opinion_builder.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/topics` | Get topics list (with filtering, sorting, pagination) |
| `GET` | `/api/v1/topics/{topic_id}` | Get single topic details |
| `GET` | `/api/v1/topics/search` | Search topics by keyword |
| `POST` | `/api/v1/topics/filter` | Advanced filter topics |
| `GET` | `/health` | Health check (with WebSocket status) |

## Quick Test

```bash
# Get topics
curl "http://localhost:8000/api/v1/topics?limit=10"

# Search topics
curl "http://localhost:8000/api/v1/topics/search?q=Bitcoin"

# Health check
curl "http://localhost:8000/health"
```

## Development

```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check .
uv run ruff format .

# Type check (if using mypy)
uv run mypy opinion_builder/
```

## Environment Variables

See `.env.example` for all available configuration options.

Required variables:
- `OPINION_SDK_API_KEY`: Opinion.trade API key
- `OPINION_WS_API_KEY`: Opinion.trade WebSocket API key
