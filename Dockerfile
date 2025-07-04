FROM python:3.9-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Cache buster: 2025-07-02 21:35:00
COPY . .

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TOKENIZERS_PARALLELISM=false

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit with optimized settings
CMD ["streamlit", "run", "app.py",      "--server.port=8080",      "--server.address=0.0.0.0",      "--server.headless=true",      "--server.fileWatcherType=none",      "--browser.gatherUsageStats=false",      "--server.enableCORS=false",      "--server.enableXsrfProtection=false",      "--server.maxUploadSize=50",      "--server.maxMessageSize=50"]