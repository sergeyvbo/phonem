# Production Dockerfile for Hugging Face Spaces
# This Dockerfile is intended to be in the root of the project

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENV prod

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Create data directories with permissions
RUN mkdir -p /tmp/data/inputs /tmp/data/outputs && chmod -R 777 /tmp/data

# Hugging Face Spaces listen on port 7860
EXPOSE 7860

# Run the application
# We need to run from the root of the backend folder's structure (where 'app' is found)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
