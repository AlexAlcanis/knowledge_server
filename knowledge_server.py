import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# --- YOUR TOOLS ---
@mcp.tool()
def search_docs(query: str) -> str:
    """Useful for searching the knowledge base."""
    return f"Searching for: {query}. Connection is active!"

# 2. THE HANDSHAKE FIX: Catch the AWS 'initialized' ping
async def handle_mcp_post(request):
    try:
        body = await request.json()
        # AWS sends 'notifications/initialized' to check if you are an MCP server
        # We MUST return a successful JSON-RPC response or it fails the Sync
        if body.get("method") == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "result": "ok", "id": body.get("id")})
    except Exception:
        pass
    
    # For everything else, use the standard FastMCP handler
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Explicit Starlette App (Ensures Lifespan/Startup signals reach MCP)
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"])
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    # lifespan="on" is mandatory to wake up the MCP task groups
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
