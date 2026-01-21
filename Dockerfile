FROM python:3.10-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p uploads exports processing

# Expose port (optional, but good practice)
EXPOSE 8000

# Start script
CMD ["sh", "-c", "./start_worker.sh & uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
