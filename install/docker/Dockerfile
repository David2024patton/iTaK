# iTaK — Dockerfile
# Build stage for the main agent container

FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    jq \
    nodejs \
    npm \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY install/requirements/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for browser-use)
RUN playwright install chromium --with-deps 2>/dev/null || true

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/db data/logs

# Non-root user for security
RUN useradd -m -s /bin/bash itak && chown -R itak:itak /app
USER itak

# Default entry point
ENTRYPOINT ["python", "-m", "app.main"]
CMD ["--adapter", "cli"]
