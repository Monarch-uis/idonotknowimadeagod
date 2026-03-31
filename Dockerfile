# Multi-stage Dockerfile for EPUB to Audiobook/Video Converter
# Stage 1: Build environment
FROM python:3.14-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime environment
FROM python:3.14-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash epubuser && \
    mkdir -p /app/logs /app/output /app/Novels /app/_NEW_EPUBS_HERE && \
    chown -R epubuser:epubuser /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=epubuser:epubuser . /app/

# Copy Piper TTS binaries and models if they exist
COPY --chown=epubuser:epubuser piper/ /app/piper/
COPY --chown=epubuser:epubuser piper_models/ /app/piper_models/

# Switch to non-root user
USER epubuser

# Create log directory structure
RUN mkdir -p logs/main logs/tts logs/video logs/errors logs/profiling logs/recovery

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "epub_project_manager.py"]
