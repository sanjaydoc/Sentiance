# Sentiance

A small, production-shaped **FastAPI** service for text sentiment analysis.

It ships with a dependency-free, lexicon-based analyzer so the project runs and
tests out of the box — swap in a real model (transformer, hosted API, etc.)
behind the same interface without touching the HTTP layer.

## Features

- **FastAPI** app with automatic OpenAPI docs at `/docs`.
- Single and batch analysis endpoints.
- Typed request/response models with **Pydantic v2**.
- Environment-based configuration via **pydantic-settings**.
- Tests with **pytest** + coverage, linting with **ruff**.
- **Dockerfile**, **docker-compose**, and a **GitHub Actions** CI pipeline.

## Project layout

```
app/
  __init__.py       # package + version
  __main__.py       # `python -m app` / `sentiance` entry point
  config.py         # Settings (SENTIANCE_* env vars)
  main.py           # app factory + ASGI `app`
  routes.py         # HTTP endpoints
  schemas.py        # Pydantic models
  sentiment.py      # the analyzer (swap-in point)
tests/              # pytest suite
Dockerfile
docker-compose.yml
.github/workflows/ci.yml
```

## Quickstart

```bash
# 1. Create a virtual environment and install (with dev extras)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Run the service (hot reload in development)
python -m app
# or
uvicorn app.main:app --reload

# 3. Open the interactive docs
open http://localhost:8000/docs
```

## API

### `GET /health`

```json
{ "status": "ok", "app": "Sentiance", "version": "0.1.0", "environment": "development" }
```

### `POST /analyze`

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product!"}'
```

```json
{ "text": "I love this product!", "sentiment": "positive", "score": 0.2 }
```

### `POST /analyze/batch`

```bash
curl -X POST http://localhost:8000/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["I love it", "I hate it", "it exists"]}'
```

## Configuration

Settings are read from the environment (prefix `SENTIANCE_`) or a local `.env`
file. See [`.env.example`](.env.example).

| Variable                  | Default       | Description                       |
| ------------------------- | ------------- | -------------------------------- |
| `SENTIANCE_APP_NAME`      | `Sentiance`   | Service name shown in docs/health |
| `SENTIANCE_ENVIRONMENT`   | `development` | `development` enables hot reload  |
| `SENTIANCE_LOG_LEVEL`     | `INFO`        | uvicorn log level                 |

## Development

```bash
pytest          # run tests with coverage
ruff check .    # lint
ruff format .   # format
```

## Docker

```bash
docker compose up --build
# service available at http://localhost:8000
```

## Swapping in a real model

`app/sentiment.py` exposes a `SentimentAnalyzer` with a single
`analyze(text) -> AnalyzeResponse` method and a module-level `analyzer`
singleton used by the routes. Replace the implementation (e.g. load a
Hugging Face pipeline or call an external API) while keeping that interface and
the rest of the app is unchanged.

## License

MIT — see [LICENSE](LICENSE).
