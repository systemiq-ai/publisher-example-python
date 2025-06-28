# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first for better caching
COPY requirements.txt ./

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application files
COPY . /app

# Set environment variables
ENV ENVIRONMENT=production
ENV OBSERVER_ENDPOINT=localhost:50051
ENV OTEL_EXPORTER_OTLP_ENDPOINT=
ENV PYTHONPATH="/app:/app/protos"
ENV GRPC_VERBOSITY=ERROR

# Use JSON format for CMD to prevent OS signal issues
CMD ["/bin/sh", "-c", "if [ \"$ENVIRONMENT\" = \"development\" ]; then \
      echo 'Starting in development mode with auto-reload...' && \
      watchmedo auto-restart --directory=./ --patterns=\"*.py\" --recursive -- python main.py; \
    else \
      echo 'Starting in production mode...' && \
      python main.py; \
    fi"]