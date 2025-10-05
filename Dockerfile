# Dockerfile for Minecraft Wiki Bot
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY wiki_scraper.py .
COPY vector_db.py .
COPY rag_pipeline.py .
COPY cache_manager.py .
COPY nextcloud_bot.py .

# Create necessary directories
RUN mkdir -p wiki_data chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the bot
CMD ["uvicorn", "nextcloud_bot:app", "--host", "0.0.0.0", "--port", "8000"]
