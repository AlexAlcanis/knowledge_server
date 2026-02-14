from flask import Flask, jsonify
from fastmcp import FastMCP
from a2wsgi import ASGIMiddleware, WSGIMiddleware
import uvicorn
import os
import httpx
from bs4 import BeautifulSoup

# 1. Setup Flask
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "mcp_endpoint": "/mcp",
        "knowledge_base_path": os.path.abspath("./knowledge_base")
    })

# 2. Setup MCP
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
    """Reads a specific file from the 'knowledge_base' folder."""
    base_path = "./knowledge_base"
    # Create the folder if it doesn't exist so the tool doesn't crash
    if not os.path.exists(base_path): os.makedirs(base_path)
    
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        return f"Error: {filename} not found. Available: {os.listdir(base_path)}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 3. The ASGI Dispatcher (with Lifespan Fix)
mcp_app = mcp.http_app()

async def asgi_app(scope, receive, send):
    if scope["type"] == "lifespan":
        async with mcp_app.lifespan(scope):
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
    
    if scope["type"] == "http":
        if scope["path"].startswith("/mcp"):
            await mcp_app(scope, receive, send)
        else:
            await WSGIMiddleware(flask_app)(scope, receive, send)

if __name__ == "__main__":
    # Ensure the knowledge folder exists before starting
    if not os.path.exists("./knowledge_base"):
        os.makedirs("./knowledge_base")
    
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000, lifespan="on")