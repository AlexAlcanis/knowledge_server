import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# --- YOUR TOOLS ---
@mcp.tool()
def read_knowledge_base() -> str:
    """A test tool to verify the connection."""
    return "Handshake successful. The MCP server is synchronized with Bedrock!"

# 2. THE HANDSHAKE FIX: Catch the AWS 'initialized' ping manually
async def handle_mcp_post(request):
    try:
        body = await request.json()
        
        # FIX: If method is notifications/initialized, we MUST return a 200/202 
        # and NOT an error -32601. This is a notification, so it has no 'id'.
        if body.get("method") == "notifications/initialized":
            return Response(status_code=202) # Accept it and return nothing (Option 2)
            
    except Exception:
        pass
    
    # For all other calls (initialize, tools/list, etc.), use the MCP handler
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App (The Gateway Shield)
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    # This wakes up the MCP task group so tools actually work
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # lifespan="on" is mandatory for MCP background tasks
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
