import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse
from starlette.routing import Route

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    """Verifies that the tool discovery is working."""
    return "Handshake Successful! The MCP server and Bedrock Gateway are now synchronized."

# 2. THE HANDSHAKE SHIELD: Intercept raw bytes to satisfy AWS out-of-order ping
async def handle_mcp_post(request):
    # Read raw bytes to catch the 'notifications/initialized' string 
    # regardless of JSON formatting or protocol order.
    body_bytes = await request.body()

    if b'"method":"notifications/initialized"' in body_bytes:
        # AWS sends this before 'initialize'. We say 'OK' to satisfy the sync.
        return Response(status_code=200)

    # For all other valid MCP calls, we pass the request to the underlying 
    # MCP ASGI application using the standard ASGI interface.
    mcp_app = mcp.http_app(stateless_http=True)
    return await mcp_app(request.scope, request.receive, request._send)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App with explicit lifespan
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    # This ensures background tasks/tool groups are initialized
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # lifespan="on" is mandatory for MCP servers
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
