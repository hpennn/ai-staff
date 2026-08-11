FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Chinese fonts
RUN apt-get update && apt-get install -y --no-install-recommends     fonts-noto-cjk     tesseract-ocr     tesseract-ocr-chi-sim     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "backend/main.py"]
