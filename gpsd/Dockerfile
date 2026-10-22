FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /uvx /bin/

# Python project installation
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip install -r requirements.txt

# Add non-root user
RUN adduser --disabled-password appuser

COPY . .

# fix perms
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
