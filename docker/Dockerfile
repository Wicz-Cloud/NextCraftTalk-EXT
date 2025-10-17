# Dockerfile for Minecraft Wiki Bot
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (faster than pyproject.toml)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy pyproject.toml for metadata
COPY pyproject.toml .

# Copy application code
COPY src/ ./src/

# Create necessary directories
RUN mkdir -p wiki_data chroma_db logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c "python -c \"import requests; requests.get(f'http://localhost:\${BOT_PORT}/health')\"" || exit 1

# Run the bot
CMD ["python", "-m", "src.bot.api"]
