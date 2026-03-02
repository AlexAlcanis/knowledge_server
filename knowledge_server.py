import os
import uvicorn
import json
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

# 1. Use FastMCP ONLY for defining tools, NOT for the server
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    """Simple test tool."""
    return "The handshake is finally complete!"

# 2. THE RAW PROTOCOL HANDLER
# This intercepts the AWS ping BEFORE it hits the MCP library's 'strict' mode
async def handle_mcp_post(request):
    try:
        body = await request.json()
        
        # Check if this is the 'initialized' notification from AWS
        if body.get("method") == "notifications/initialized":
            # Per JSON-RPC spec, notifications shouldn't get a body response.
            # Returning a 200 OK satisfies the Gateway's check.
            return Response(status_code=200)
            
        # For all other methods (initialize, tools/list), use the MCP engine
        return await mcp.handle_http_request(request)
            
    except Exception as e:
        return JSONResponse({"error": "Invalid JSON-RPC"}, status_code=400)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App
# We define /mcp as a Route so our 'handle_mcp_post' is the boss.
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    # This wakes up the MCP background tasks
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Uvicorn is mandatory; Gunicorn will not work here.
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
