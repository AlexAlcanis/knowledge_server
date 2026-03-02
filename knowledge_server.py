import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

# 1. Initialize FastMCP (strictly for defining tools)
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    """A test tool to verify connection."""
    return "Handshake Successful! The Gateway and Server are synced."

# 2. THE HANDSHAKE SHIELD: Catch the AWS ping BEFORE the library does
async def handle_mcp_post(request):
    try:
        body = await request.json()
        # If AWS sends 'notifications/initialized', we MUST return 200 OK.
        # This bypasses the -32601 "Method not found" error.
        if body.get("method") == "notifications/initialized":
            return Response(status_code=200)
    except Exception:
        pass
    
    # For all other calls (tools/list, tools/call), use the MCP engine
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App manually to control the /mcp route
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    # This wakes up the MCP background task groups
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Uvicorn is MANDATORY. Gunicorn will cause the handshake to fail.
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
