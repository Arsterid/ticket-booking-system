FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /uvx /bin/

WORKDIR /backend

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-editable

RUN mv .venv .venv-dev

RUN uv sync --frozen --no-dev --no-editable
RUN mv .venv .venv-prod


FROM python:3.14-slim AS development
WORKDIR /backend

COPY --from=builder /backend/.venv-dev /backend/.venv

COPY . .

ENV PATH="/backend/.venv/bin:$PATH"


FROM python:3.14-slim AS final
WORKDIR /backend

COPY --from=builder /backend/.venv-prod /backend/.venv

COPY . .

ENV PATH="/backend/.venv/bin:$PATH"
