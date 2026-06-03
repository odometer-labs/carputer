FROM python:3.13-alpine AS builder

RUN pip3 install uv==0.10.2

WORKDIR /app

COPY pyproject.toml .

RUN uv pip install --system --no-cache-dir .

COPY main.py .

COPY wifi_manager.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9001"]
