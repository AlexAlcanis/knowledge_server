import os
import asyncio
import uvicorn
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# 1. Initialize the Server Logic
# We use FastMCP as the "engine" for tools, but wrap it in a compliant Starlette app
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    """Simple test tool."""
    return "Protocol Handshake Successful! Gateway is connected."

# 2. THE FIX: Create the Starlette App and handle the HTTP Handshake manually
# This ensures that 'notifications/initialized' does NOT return a -32601 error.
async def handle_mcp_request(request):
    # This uses the underlying MCP handle_http_request which is 
    # compatible with the latest SDK lifecycle.
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        # The Gateway pings this endpoint for the full MCP lifecycle
        Route("/mcp", endpoint=handle_mcp_request, methods=["POST"]),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # We run with uvicorn to support the ASGI lifespan
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
