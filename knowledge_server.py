import os
import httpx
from flask import Flask, jsonify
from fastmcp import FastMCP
from bs4 import BeautifulSoup
from a2wsgi import ASGIMiddleware
import uvicorn

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase")

# --- TOOL 1: Read Web Links ---
@mcp.tool()
async def read_link(url: str) -> str:
    """Fetches text content from a web link for context."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            for s in soup(["script", "style"]): s.extract()
            return soup.get_text(separator=' ', strip=True)[:5000]
    except Exception as e:
        return f"Error fetching link: {str(e)}"

# --- TOOL 2: Read Local Docs ---
@mcp.tool()
def search_local_docs(filename: str) -> str:
    """Reads a specific file from the '/tmp/knowledge_base' folder."""
    base_path = "/tmp/knowledge_base"
    
    # Ensure directory exists so we don't 500
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
    
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        try:
            files = os.listdir(base_path)
            return f"Error: {filename} not found. Available files: {files}"
        except Exception:
            return f"Error: {filename} not found and folder is inaccessible."
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 2. Setup Flask for Root Health Check
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return jsonify({"status": "online", "mcp_path": "/mcp"})

# 3. Create the ASGI App
# MANDATORY: stateless_http=True for Bedrock AgentCore
mcp_app = mcp.http_app(stateless_http=True)

async def asgi_app(scope, receive, send):
    if scope["type"] == "http" and scope["path"].startswith("/mcp"):
        # Wrap in try/except to prevent 500s from killing the handshake
        try:
            await mcp_app(scope, receive, send)
        except Exception as e:
            print(f"MCP Error: {e}")
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [[b"content-type", b"text/plain"]]
            })
            await send({"type": "http.response.body", "body": str(e).encode()})
    else:
        await ASGIMiddleware(flask_app)(scope, receive, send)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # We use 0.0.0.0 so App Runner can route external traffic to the container
    uvicorn.run(asgi_app, host="0.0.0.0", port=port)
