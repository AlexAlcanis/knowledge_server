import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# 2. THE HANDSHAKE FIX: Explicitly allow POST and GET
async def handle_mcp_request(request):
    # Handle the AWS "initialized" ping
    try:
        if request.method == "POST":
            body = await request.json()
            if body.get("method") == "notifications/initialized":
                return JSONResponse({"jsonrpc": "2.0", "result": "ok", "id": body.get("id")})
    except:
        pass
    
    # Pass everything else to the MCP handler
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App with flexible routing
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        # Catch both /mcp and /mcp/ to avoid 'Method Not Allowed' errors
        Route("/mcp", endpoint=handle_mcp_request, methods=["GET", "POST", "OPTIONS"]),
        Route("/mcp/", endpoint=handle_mcp_request, methods=["GET", "POST", "OPTIONS"]),
        Mount("/mcp", app=mcp.http_app(stateless_http=True))
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

@mcp.tool()
def hello_world() -> str:
    """Verifies connection."""
    return "The Gateway and MCP server are now perfectly synced!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
