FROM python:3.14 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /uvx /bin/

WORKDIR /backend

COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --frozen --no-dev

RUN mv .venv .venv-prod

RUN uv sync --frozen

FROM python:3.14 as development
WORKDIR /backend

COPY --from=builder /backend/.venv /backend/.venv
COPY . .

ENV PATH="/backend/.venv/bin:$PATH"

FROM python:3.14 AS final

WORKDIR /backend

COPY --from=builder /backend/.venv-prod /backend/.venv
COPY ./src ./src

ENV PATH="/backend/.venv/bin:$PATH"
