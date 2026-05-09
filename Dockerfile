# ---- build stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir "." --target /app/packages

# ---- production stage ----
FROM python:3.11-slim AS production

WORKDIR /app

COPY --from=builder /app/packages /app/packages
COPY src/ /app/src/

ENV PYTHONPATH=/app/packages:/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]
