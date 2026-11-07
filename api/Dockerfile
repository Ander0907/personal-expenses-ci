# syntax=docker/dockerfile:1.28.0

# ---- Stage 1: builder -------------------------------------------------------
# Installs runtime dependencies into an isolated virtualenv.
FROM python:3.12.16-slim-bookworm AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the dependency manifests first so this layer is cached
# until requirements or constraints change.
COPY requirements.txt constraints.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -c constraints.txt

# ---- Stage 2: runtime -------------------------------------------------------
# Minimal image: the prebuilt venv plus application code, running as non-root.
FROM python:3.12.16-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="personal-expenses-api" \
      org.opencontainers.image.description="FastAPI service for the personal expenses tracker" \
      org.opencontainers.image.source="https://github.com/Ander0907/personal-expenses-ci"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Fixed UID/GID, no home directory and no login shell.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# WORKDIR must contain alembic.ini (it relies on prepend_sys_path = .).
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
# Code stays root-owned and read-only for the runtime user.
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

USER app
EXPOSE 8000

# Python stdlib probe (slim has no curl). Timeout exceeds the 3s DB connect timeout.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"]

# Apply migrations, then replace the shell with uvicorn so it receives signals.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
