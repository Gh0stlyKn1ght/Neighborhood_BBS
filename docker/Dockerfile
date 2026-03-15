FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY web/ ./web/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p data logs

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=src/server.py
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8080

# Run initialization and start server
CMD python scripts/init_db.py && python src/main.py
