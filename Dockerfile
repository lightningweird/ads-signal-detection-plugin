FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone and setup ads-anomaly-detection
RUN git clone https://github.com/lightningweird/ads-anomaly-detection.git
RUN cd ads-anomaly-detection && pip install redis aioredis numpy scipy pandas structlog fastapi uvicorn websockets aiofiles pyyaml python-dotenv prometheus-client psutil

# Copy application code
COPY src/ ./src/
COPY plugins/ ./plugins/
COPY config.yaml .
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install -e .

# Create directories
RUN mkdir -p logs /tmp/signal_detector/overflow

# Expose ports
EXPOSE 8080 9090

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.yaml
ENV PYTHONPATH=/app:/app/ads-anomaly-detection/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "-m", "src.main"]