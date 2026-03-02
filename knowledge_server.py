import os
import json
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, Response

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# 2. THE HANDSHAKE FIX: Catch the AWS 'initialized' ping manually
async def handle_mcp_post(request):
    try:
        body = await request.json()
        
        # AWS sends 'notifications/initialized' (a notification has no 'id')
        # We MUST return a 200 OK (empty) or a 202 Accepted to satisfy the Gateway
        if body.get("method") == "notifications/initialized":
            # Per JSON-RPC spec, notifications shouldn't get a response,
            # but AWS Gateway often requires a 200 OK to complete the sync.
            return Response(status_code=200)
            
    except Exception:
        pass
    
    # For all other tool calls, pass to the FastMCP handler
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Explicit Starlette App (The Shield)
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"])
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

@mcp.tool()
def hello_world() -> str:
    """A test tool to verify the connection is alive."""
    return "Success! The MCP server and Bedrock Gateway are now synchronized."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
