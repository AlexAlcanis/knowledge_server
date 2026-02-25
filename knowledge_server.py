import os
import httpx
from flask import Flask, jsonify
from fastmcp import FastMCP
from bs4 import BeautifulSoup
from a2wsgi import ASGIMiddleware
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase")

# --- TOOLS ---
@mcp.tool()
async def read_link(url: str) -> str:
    """Fetches text content from a web link."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)[:5000]

@mcp.tool()
def search_local_docs(filename: str) -> str:
    """Reads a file from /tmp/knowledge_base."""
    base_path = "/tmp/knowledge_base"
    if not os.path.exists(base_path): 
        os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path): 
        return f"Error: {filename} not found."
    with open(file_path, 'r', encoding='utf-8') as f: 
        return f.read()

# 2. Setup Flask (Health check & status)
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return jsonify({"status": "online", "mcp_endpoint": "/mcp"})

# 3. Create the MCP ASGI App
mcp_app = mcp.http_app(stateless_http=True)

# 4. The Starlette Wrapper (The Fix)
# This Mounts your MCP app and Flask app while preserving the Lifespan signal
app = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=ASGIMiddleware(flask_app))
    ],
    lifespan=mcp_app.lifespan  # Crucial: Tells the server to initialize MCP task groups
)

if __name__ == "__main__":
    # App Runner provides the port via an environment variable. 
    # If it's not there, we default to 8080 to match your AWS settings.
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🚀 Starting server on 0.0.0.0:{port}")
    # Use lifespan="on" to ensure FastMCP initializes correctly
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")

