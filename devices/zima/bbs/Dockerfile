# Neighborhood BBS - Docker Image
# Multi-stage build for minimal final image

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 bbs && chown -R bbs:bbs /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/bbs/.local

# Copy application files
COPY --chown=bbs:bbs . .

# Set environment variables
ENV PATH=/home/bbs/.local/bin:$PATH \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    ADMIN_PASSWORD=gh0stly \
    LISTEN_PORT=5000

# Create volume for persistent database
VOLUME ["/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${LISTEN_PORT}/health || exit 1

# Switch to non-root user
USER bbs

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
