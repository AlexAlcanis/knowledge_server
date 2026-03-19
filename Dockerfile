FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make the startup script executable
RUN chmod +x start_services.sh

# Expose both ports
EXPOSE 8080
EXPOSE 8501

# Run both services
CMD ["./start_services.sh"]
