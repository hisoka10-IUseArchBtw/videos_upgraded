FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download and cache the nomic-embed-text-v1.5 model to avoid network fetches at runtime
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='nomic-ai/nomic-embed-text-v1.5')"

# Copy the backend code
COPY backend/ ./backend/

# Expose the API port
EXPOSE 8000

# The default command will be overridden by docker-compose for the worker
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
