FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose web server port
EXPOSE 8080

# Run both bot + web server
CMD ["python", "run_all.py"]
