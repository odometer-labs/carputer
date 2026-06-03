FROM python:3.13-alpine AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /uvx /bin/

# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

WORKDIR /app
RUN uv sync --locked

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9001"]
