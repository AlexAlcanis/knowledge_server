FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
# Launch using the asgi_app variable we defined
CMD ["uvicorn", "knowledge_server:asgi_app", "--host", "0.0.0.0", "--port", "8080"]
