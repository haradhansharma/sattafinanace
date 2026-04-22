# meridian/idback/backend/Dockerfile

# Use a slim, stable Python image
FROM python:3.11-slim

# Set environment variables to optimize Python performance
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# System dependencies for psycopg2-binary and others
# libpq-dev is for PostgreSQL headers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

# --- ADD NON-ROOT USER ---
# Create a user named 'appuser' with a home directory
RUN useradd -ms /bin/bash appuser

# Create directories and set permissions for the non-root user
# -------------------------------------------------------------
# Create the logs directory if it doesn't exist
RUN mkdir -p /app/logs
# Change ownership of the logs directory to the newly created 'appuser'
RUN chown -R appuser:appuser /app

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the actual backend code
COPY . .

# 3. Fix permissions for the whole app folder
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# --- SWITCH TO NON-ROOT USER ---
USER appuser

# Expose port (Nginx reverse proxy will map to this)
EXPOSE 8086

# The production startup command: Gunicorn orchestrating Uvicorn
# myproject.asgi:application assumes your Django project name is 'myproject'
CMD ["gunicorn", "--bind", "0.0.0.0:8086", "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "config.asgi:application"]