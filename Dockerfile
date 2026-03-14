FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 1. Force Playwright to use a specific, stable directory
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright
# 2. Ensure Python doesn't buffer logs so you can see errors immediately
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project

# 3. Install browsers into the location defined in ENV above
RUN uv run playwright install --with-deps chromium

COPY . .
