# Use a stable official Python slim runtime as the parent image
FROM python:3.11-slim

# Set system-level environment variables
# Prevents Python from writing pyc files to disk and keeps stdout/stderr unbuffered for Docker logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set the working directory in the container
WORKDIR /code

# Install system dependencies
# - curl: needed for container orchestration health checks
# - libgomp1: REQUIRED for FAISS-CPU C++ bindings on Linux platforms
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements manifest
COPY requirements.txt /code/

# Install python dependencies without caching packages to reduce layer size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application package source code
COPY app /code/app

# Pre-initialize persistent data directories
RUN mkdir -p /code/data/uploads /code/data/vectorstore

# Expose target server port
EXPOSE 8000

# Set health probe endpoint check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Define execution startup command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
