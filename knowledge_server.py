import os
import httpx
from flask import Flask, jsonify
from fastmcp import FastMCP
from bs4 import BeautifulSoup
from a2wsgi import ASGIMiddleware
import uvicorn

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase")

# --- TOOLS (Keep these simple for the sync) ---
@mcp.tool()
async def read_link(url: str) -> str:
    """Fetches text content from a web link."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)[:5000]

# 2. Setup Flask for Health Checks
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return jsonify({"status": "online", "mcp_endpoint": "/mcp"})

# 3. Create the ASGI App with explicitly defined path handling
mcp_app = mcp.http_app(stateless_http=True)

async def asgi_app(scope, receive, send):
    # This captures /mcp AND /mcp/ to prevent Gateway 404s
    path = scope.get("path", "").rstrip("/")
    
    if scope["type"] == "http" and path == "/mcp":
        await mcp_app(scope, receive, send)
    else:
        # Route to Flask for the root health check
        await ASGIMiddleware(flask_app)(scope, receive, send)

if __name__ == "__main__":
    # App Runner provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # Must bind to 0.0.0.0 for App Runner to work
    uvicorn.run(asgi_app, host="0.0.0.0", port=port)
