# Dockerfile for containerized distribution

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs templates

# Expose dashboard port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DASHBOARD_PORT=8080

# Run the agent
CMD ["python", "main.py"]

