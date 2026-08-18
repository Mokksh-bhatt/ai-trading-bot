FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
# Note: we expect the docker build context to be the project root
COPY backend/ ./backend/

# Expose port
EXPOSE 8001

# Command to run the backend
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8001}
