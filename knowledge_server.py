import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    """Verifies connection."""
    return "Sync successful! The MCP server is responding."

# 2. THE ULTIMATE HANDSHAKE FIX
async def handle_mcp_universal(request):
    # Log for your visibility in App Runner logs
    print(f"Received {request.method} request to {request.url.path}")

    # A. Catch the AWS 'initialized' notification (POST)
    if request.method == "POST":
        body = await request.body()
        if b"notifications/initialized" in body:
            return Response(status_code=200, content="ok")

    # B. Support GET requests (AWS sometimes pings GET /mcp for health)
    if request.method == "GET":
        return JSONResponse({"status": "mcp_active", "transport": "http"})

    # C. Pass everything else to the MCP engine
    mcp_app = mcp.http_app(stateless_http=True)
    return await mcp_app(request.scope, request.receive, request._send)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Flexible Routing: Catch /mcp, /mcp/, and any method
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_universal, methods=["GET", "POST", "OPTIONS"]),
        Route("/mcp/", endpoint=handle_mcp_universal, methods=["GET", "POST", "OPTIONS"]),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
