FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use a shell script to run migrations then exec into Python for proper signal handling
CMD ["sh", "-c", "alembic upgrade head && exec python main.py"]