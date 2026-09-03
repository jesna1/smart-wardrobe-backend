FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and force stdout/stderr buffering to show logs instantly on Render
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install C-compilers and PostgreSQL client libraries required for DB drivers (asyncpg/psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 10000

# Run Alembic DB migrations automatically on deploy, then start Gunicorn with multi-worker Uvicorn
CMD ["sh", "-c", "alembic upgrade head && gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT:-10000}"]