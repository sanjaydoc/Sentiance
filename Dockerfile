FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md ./
COPY sentiance ./sentiance
RUN pip install --upgrade pip && pip install ".[kafka]"

EXPOSE 8000

# Run as a non-root user.
RUN useradd --create-home appuser
USER appuser

# Default: the all-in-one server. Compose overrides the command per service.
CMD ["uvicorn", "sentiance.app:app", "--host", "0.0.0.0", "--port", "8000"]
