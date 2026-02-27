import os
from flask import Flask, jsonify
from fastmcp import FastMCP
from a2wsgi import ASGIMiddleware
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase")

@mcp.tool()
def hello_world() -> str:
    """A simple test tool to verify MCP is working"""
    return "The MCP server is connected and working!"

@mcp.tool()
def get_server_info() -> dict:
    """Get information about the MCP server"""
    return {
        "name": "KnowledgeBase MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools_available": 2
    }

# 2. Setup Flask for Health Checks
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return jsonify({
        "status": "online", 
        "service": "MCP Knowledge Server",
        "mcp_endpoint": "/mcp"
    })

@flask_app.route("/health")
def health():
    return jsonify({"status": "healthy"})

# 3. Create the MCP ASGI App with stateless_http=True for Bedrock
mcp_app = mcp.http_app(stateless_http=True)

# 4. Create Starlette app with proper lifespan handling
app = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=ASGIMiddleware(flask_app))
    ],
    lifespan=mcp_app.lifespan  # This ensures task group is initialized
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting MCP Knowledge Server on port {port}")
    print(f"   Health check: http://0.0.0.0:{port}/")
    print(f"   MCP endpoint: http://0.0.0.0:{port}/mcp")
    
    # Run with lifespan enabled
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        lifespan="on",  # Critical: enables lifespan events
        log_level="info"
    )
