FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 1. Enable bytecode compilation for faster Python execution
ENV UV_COMPILE_BYTECODE=1

# 2. Copy ONLY the dependency tracking files first
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

# Final fast sync to register your app package layout if applicable
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000 

CMD ["uv", "run", "fastapi", "dev", "main.py", "--host", "0.0.0.0", "--port", "8000"]