FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default port (Railway overrides via env)
ENV PORT=8080

# Start web dashboard
CMD ["sh", "-c", "uvicorn web:app --host 0.0.0.0 --port $PORT"]
