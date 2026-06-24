FROM python:3.14-slim AS base-builder
COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /uvx /bin/

WORKDIR /backend
COPY pyproject.toml uv.lock ./


FROM base-builder AS test-env-builder
RUN uv sync --frozen --no-dev --group test --no-editable


FROM base-builder AS lint-env-builder
RUN uv sync --frozen --no-dev --group lint --no-editable


FROM base-builder AS prod-env-builder
RUN uv sync --frozen --no-dev --no-editable


FROM python:3.14-slim AS tests
WORKDIR /backend

COPY --from=test-env-builder /backend/.venv /backend/.venv

COPY . .

ENV PATH="/backend/.venv/bin:$PATH"


FROM python:3.14-slim AS lint
WORKDIR /backend

COPY --from=lint-env-builder /backend/.venv /backend/.venv

COPY . .

ENV PATH="/backend/.venv/bin:$PATH"


FROM python:3.14-slim AS backend
WORKDIR /backend

COPY --from=prod-env-builder /backend/.venv /backend/.venv

COPY . .

ENV PATH="/backend/.venv/bin:$PATH"
