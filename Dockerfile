FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the standard App Runner port
EXPOSE 8080

# Run ONLY the MCP server (not the shell script)
CMD ["python", "knowledge_server.py"]

