FROM python:3.13-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /uvx /bin/

RUN apt-get update && apt-get install -y curl

# Python project installation
RUN uv pip install "psycopg[binary]"
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip install -r requirements.txt



# Add non-root user
RUN adduser --disabled-password appuser

COPY . .

# fix perms
RUN chown -R appuser:appuser /app

ENV PORT=8888
EXPOSE 8888

# Switch to non-root user
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]