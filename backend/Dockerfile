# Production image for the Shoebox FastAPI backend.
#
# Two-stage build to keep the final image small. Stage 1 installs the Python
# dependencies into a virtualenv; stage 2 copies that venv + the source onto
# a slim base. Resulting image ~140 MB.
#
# Build:  docker build -t shoebox-api:latest .
# Run:    docker run --rm -p 8000:8000 --env-file .env.prod shoebox-api:latest

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps for asyncpg + cryptography wheels; removed in the final stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip wheel \
 && /opt/venv/bin/pip install -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# libpq for asyncpg + curl for the healthcheck only — no compiler in prod.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --shell /bin/bash shoebox

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=shoebox:shoebox . .

USER shoebox

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/ || exit 1

# Run alembic upgrade before uvicorn so a fresh container always lands on
# the latest schema. `alembic upgrade head` is idempotent.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips='*'"]
