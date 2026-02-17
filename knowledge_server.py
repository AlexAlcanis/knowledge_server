import os
import httpx
from flask import Flask, jsonify
from fastmcp import FastMCP
from bs4 import BeautifulSoup
from a2wsgi import ASGIMiddleware
import uvicorn

# 1. Setup MCP with Stateless HTTP
# stateless_http=True is crucial for Bedrock AgentCore
mcp = FastMCP("KnowledgeBase", host="0.0.0.0", stateless_http=True)

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
    """Reads a specific file from the 'knowledge_base' folder."""
    base_path = "./knowledge_base"
    if not os.path.exists(base_path): os.makedirs(base_path)
    
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        return f"Error: {filename} not found. Available: {os.listdir(base_path)}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 2. Setup Flask (Optional Status Page)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "mcp_endpoint": "/mcp",
        "knowledge_base_path": os.path.abspath("./knowledge_base")
    })

# 3. The Unified ASGI App
# This ensures that Bedrock sees the /mcp endpoint correctly
mcp_app = mcp.http_app()

async def asgi_handler(scope, receive, send):
    if scope["type"] == "http" and scope["path"].startswith("/mcp"):
        await mcp_app(scope, receive, send)
    else:
        # Fallback to Flask for the home page status
        await ASGIMiddleware(flask_app)(scope, receive, send)

if __name__ == "__main__":
    if not os.path.exists("./knowledge_base"):
        os.makedirs("./knowledge_base")
        
    # Standard port for App Runner/Bedrock integration is 8000 or 8080
    uvicorn.run(asgi_handler, host="0.0.0.0", port=8080)

