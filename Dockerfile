# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source
COPY frontend ./

# Build React app
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

# Prevents Python from writing .pyc files and ensures output is flushed
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Node.js for serving frontend
RUN apt-get update && apt-get install -y nodejs npm curl && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend ./backend

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/build ./frontend/build
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/

# Install serve globally for serving the React build
RUN npm install -g serve

# Copy startup script
COPY start.sh ./start.sh

# Make startup script executable
RUN chmod +x start.sh

# Expose ports for tool_api (8000), agent_api (8001), and frontend (3000)
EXPOSE 8000 8001 3000

# Default command runs all services via start.sh
CMD ["./start.sh"]
