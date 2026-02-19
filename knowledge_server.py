import os
import httpx
from flask import Flask, jsonify
from fastmcp import FastMCP
from bs4 import BeautifulSoup
from a2wsgi import ASGIMiddleware
import uvicorn

# 1. Initialize FastMCP (Metadata only)
mcp = FastMCP("KnowledgeBase")

# --- TOOL 1: Read Web Links ---
@mcp.tool()
async def read_link(url: str) -> str:
    """Fetches text content from a web link for context."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')
        for s in soup(["script", "style"]): s.extract()
        return soup.get_text(separator=' ', strip=True)[:5000]

# --- TOOL 2: Read Local Docs ---
@mcp.tool()
def search_local_docs(filename: str) -> str:
    """Reads a specific file from the '/tmp/knowledge_base' folder."""
    # App Runner root is read-only; use /tmp for runtime file operations
    base_path = "/tmp/knowledge_base"
    if not os.path.exists(base_path): 
        os.makedirs(base_path, exist_ok=True)
    
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        return f"Error: {filename} not found. Available: {os.listdir(base_path)}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 2. Setup Flask (Optional Status Page)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({"status": "Online", "mcp_endpoint": "/mcp"})

# 3. Create the ASGI Application
# MOVE stateless_http=True HERE (Required for Bedrock AgentCore)
mcp_app = mcp.http_app(stateless_http=True)

# This variable MUST be named asgi_app to match your Uvicorn/App Runner settings
async def asgi_app(scope, receive, send):
    if scope["type"] == "http" and scope["path"].startswith("/mcp"):
        await mcp_app(scope, receive, send)
    else:
        # Fallback to Flask for root and health checks
        await ASGIMiddleware(flask_app)(scope, receive, send)

if __name__ == "__main__":
    # Dynamically get the port from App Runner environment
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting MCP Server on 0.0.0.0:{port}")
    uvicorn.run(asgi_app, host="0.0.0.0", port=port)
