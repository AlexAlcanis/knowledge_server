import os
import uvicorn
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, Response

# 1. Initialize FastMCP (We use it for tool definitions)
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def read_knowledge_base() -> str:
    """A test tool to verify the connection."""
    return "Handshake complete. The Knowledge Base is now synchronized!"

# 2. Setup the Starlette Wrapper to fix the Handshake
async def handle_mcp_post(request):
    try:
        body = await request.json()
        
        # FIX: Explicitly handle the 'notifications/initialized' signal
        # Bedrock Gateway sends this to verify your server exists.
        if body.get("method") == "notifications/initialized":
            # Per MCP spec, notifications get a 202 or 200 with no body
            return Response(status_code=202)
            
    except Exception:
        pass
    
    # Delegate everything else to the FastMCP engine
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the ASGI App
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
    # We must use lifespan="on" for the task groups to initialize
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
