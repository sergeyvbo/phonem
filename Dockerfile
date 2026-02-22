# Production Dockerfile for Hugging Face Spaces
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENV prod
ENV PYTHONPATH /code

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Add __init__.py to ensure it's treated as a package
RUN touch ./app/__init__.py ./app/api/__init__.py ./app/core/__init__.py ./app/services/__init__.py

# Pre-download the Allosaurus model and NLTK resources to avoid timeout on first request and ensure it works offline
RUN python -m allosaurus.bin.download_model -m eng2102
RUN python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"

# Create data directories with permissions
RUN mkdir -p /tmp/data/inputs /tmp/data/outputs && chmod -R 777 /tmp/data

# Hugging Face Spaces listen on port 7860
EXPOSE 7860

# Run the application with debug logging to see what's happening
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "debug"]
