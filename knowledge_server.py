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
    return "The MCP server is connected and working!"

# 2. Setup Flask for Health Checks
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return jsonify({"status": "online", "mcp_endpoint": "/mcp"})

# 3. Create the MCP ASGI App
# stateless_http=True is REQUIRED for Bedrock
mcp_app = mcp.http_app(stateless_http=True)

# 4. The Starlette Wrapper (The Fix)
# We use Starlette to manage the routing and the Lifespan (Startup)
app = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=ASGIMiddleware(flask_app))
    ],
    lifespan=mcp_app.lifespan  # This initializes the MCP Task Group
)

if __name__ == "__main__":
    # App Runner provides the port via environment variable
    port = int(os.environ.get("PORT", 8080))
    # We run the 'app' (Starlette), NOT a custom function
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
