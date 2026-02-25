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

# 2. Setup Flask for Health Checks
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return jsonify({"status": "online", "mcp_endpoint": "/mcp"})

# 3. Create the MCP ASGI App
mcp_app = mcp.http_app(stateless_http=True)

# 4. The Starlette Wrapper (The Fix)
# This explicitly bridges the lifespan signal to FastMCP
app = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=ASGIMiddleware(flask_app))
    ],
    lifespan=mcp_app.lifespan  # CRITICAL: This initializes the MCP task group
)

if __name__ == "__main__":
    # App Runner provides the port (usually 8080)
    port = int(os.environ.get("PORT", 8080))
    # lifespan="on" is mandatory for Uvicorn to talk to Starlette
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
