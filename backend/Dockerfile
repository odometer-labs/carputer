FROM python:3.13-alpine AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /uvx /bin/

ENV PATH="/usr/local/bin:$PATH"
ENV UV_SYSTEM_PYTHON=1

COPY geotracker /opt/geotracker

WORKDIR /opt/geotracker

RUN uv run --group dev pytest

RUN uv build --wheel

# -----------------------------------------------------------------------------
# Stage 2: Runtime - slim image with just the wheel installed
# -----------------------------------------------------------------------------
FROM python:3.13-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv in runtime for fast installs
COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /uvx /bin/

# Copy wheel from builder stage
COPY --from=builder /opt/geotracker/dist/*.whl /tmp/

# Install the wheel and runtime dependencies
RUN uv pip install --system /tmp/*.whl psycopg[binary] python-dotenv && \
    rm /tmp/*.whl

# Add non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Default command runs the geotracker CLI entry point
# (Currently just prints "Hello from geotracker!" - backend team will expand)
CMD ["geotracker"]
