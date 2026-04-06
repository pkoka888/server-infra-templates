# Project Dockerfile Template - Production Ready
# Copy to project and customize

FROM python:3.13-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.13-slim

WORKDIR /app

# Security - REQUIRED (non-root user)
RUN addgroup -g 1000 -S appuser && \
    adduser -u 1000 -S appuser -G appuser

# Copy installed packages
COPY --from=builder /root/.local /root/.local

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    USER=appuser

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8080

# Healthcheck - REQUIRED
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]