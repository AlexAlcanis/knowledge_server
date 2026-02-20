import os
import httpx
from flask import Flask, jsonify
from fastmcp import FastMCP
from bs4 import BeautifulSoup
from a2wsgi import ASGIMiddleware
import uvicorn

# 1. Initialize FastMCP (Constructor MUST be simple in v3.0+)
mcp = FastMCP("KnowledgeBase")

# --- YOUR TOOLS ---
@mcp.tool()
async def read_link(url: str) -> str:
    """Fetches text content from a web link for context."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')
        for s in soup(["script", "style"]): s.extract()
        return soup.get_text(separator=' ', strip=True)[:5000]

@mcp.tool()
def search_local_docs(filename: str) -> str:
    """Reads a specific file from the '/tmp/knowledge_base' folder."""
    base_path = "/tmp/knowledge_base"
    if not os.path.exists(base_path): 
        os.makedirs(base_path, exist_ok=True)
    
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        return f"Error: {filename} not found."
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 2. Setup Flask for Root Health Check
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    # This helps App Runner's TCP/HTTP health check pass
    return jsonify({"status": "online", "mcp_path": "/mcp"})

# 3. Create the ASGI App
# stateless_http=True is MANDATORY for Bedrock AgentCore Gateways
mcp_app = mcp.http_app(stateless_http=True)

# The handler must be named asgi_app to match your Uvicorn call
async def asgi_app(scope, receive, send):
    # Route Gateway traffic to the MCP logic
    if scope["type"] == "http" and scope["path"].startswith("/mcp"):
        await mcp_app(scope, receive, send)
    else:
        # Route everything else (like /) to Flask
        await ASGIMiddleware(flask_app)(scope, receive, send)

if __name__ == "__main__":
    # App Runner provides the PORT environment variable (defaulting to 8080)
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting MCP Server on 0.0.0.0:{port}")
    uvicorn.run(asgi_app, host="0.0.0.0", port=port)
