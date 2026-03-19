FROM python:3.11-slim

# Set environment variables for better Python behavior in containers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies if your requirements need them (like for CORS or crypto)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the script is executable and uses Linux line endings
RUN chmod +x start_services.sh

# App Runner typically looks for port 8080 by default
EXPOSE 8080

# Using the shell form to allow environment variable expansion
CMD ["./start_services.sh"]
