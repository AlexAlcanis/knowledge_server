import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, Response

# 1. Initialize FastMCP (strictly for tool definitions)
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def read_kb() -> str:
    """A test tool to verify the connection."""
    return "Handshake successful. Tools are active!"

# 2. THE FINAL HANDSHAKE FIX
async def handle_mcp_post(request):
    try:
        body = await request.json()
        method = body.get("method")
        
        # AWS sends this to 'wake up' the server. 
        # We catch it BEFORE it hits the MCP engine to avoid the -32601 error.
        if method == "notifications/initialized":
            # Per MCP spec, a notification requires no response body. 
            # Returning 200 OK satisfies the Gateway's check.
            return Response(status_code=200) 
            
        # If it's a tool call or tool listing, pass it to the MCP engine
        return await mcp.handle_http_request(request)
            
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        }, status_code=400)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App
# We define the route manually to ensure handle_mcp_post is the ONLY gatekeeper
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    # This wakes up the background task groups
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Uvicorn is mandatory; Gunicorn will cause the handshake to fail.
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
