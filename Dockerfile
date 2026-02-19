FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expose the standard App Runner port
EXPOSE 8080
CMD ["python", "knowledge_server.py"]
