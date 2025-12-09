FROM python:3.11-slim

# Prevents Python from writing .pyc files and ensures output is flushed
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy backend code
COPY backend ./backend

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy startup script
COPY start.sh ./start.sh

# Make startup script executable
RUN chmod +x start.sh

# Expose ports for both tool_api (8000) and agent_api (8001)
EXPOSE 8000 8001

# Default command runs both services via start.sh
CMD ["./start.sh"]
