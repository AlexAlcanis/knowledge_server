import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def read_knowledge_base() -> str:
    """A test tool to verify the connection is alive."""
    return "Sync successful! The MCP server is responding to tools."

# 2. THE UNIVERSAL HANDSHAKE FIX
async def handle_mcp_universal(request):
    # A. Catch the AWS 'initialized' notification (POST)
    if request.method == "POST":
        try:
            body = await request.body()
            if b"notifications/initialized" in body:
                # AWS needs a 200 OK for this specific out-of-order ping
                return Response(status_code=200, content="ok")
        except:
            pass

    # B. Support GET requests (Fixes the 405 error in your logs)
    if request.method == "GET":
        return JSONResponse({"status": "mcp_active", "transport": "http"})

    # C. Pass everything else to the MCP engine's ASGI app
    mcp_app = mcp.http_app(stateless_http=True)
    return await mcp_app(request.scope, request.receive, request._send)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Greedy Routing: Catch /mcp, /mcp/, and any variation
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        # 'methods' list covers POST (for tools) and GET/OPTIONS (for AWS discovery)
        Route("/mcp", endpoint=handle_mcp_universal, methods=["GET", "POST", "OPTIONS"]),
        Route("/mcp/{path:path}", endpoint=handle_mcp_universal, methods=["GET", "POST", "OPTIONS"]),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # lifespan="on" is mandatory to wake up the tool groups
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
