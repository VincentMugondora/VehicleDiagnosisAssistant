FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY .env.example ./.env.example
EXPOSE 8000

# Run with multiple workers for multi-core utilization
# --workers: Use CPU count (adjustable via env var)
# --limit-max-requests: Recycle workers to prevent memory leaks
# --timeout-keep-alive: Keep connections alive for connection pooling
CMD uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${WORKERS:-4} \
    --limit-max-requests 10000 \
    --timeout-keep-alive 5
