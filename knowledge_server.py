import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# --- YOUR TOOLS ---
@mcp.tool()
def read_knowledge_base() -> str:
    """A test tool to verify the connection is alive."""
    return "Success! The MCP server and Bedrock Gateway are now synchronized."

# 2. THE HANDSHAKE FIX: Force a success response for AWS
async def handle_mcp_post(request):
    try:
        body = await request.json()
        # If AWS sends 'notifications/initialized', we say 'ok' immediately.
        # This stops the -32601 'Method not found' error.
        if body.get("method") == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "result": "ok", "id": body.get("id")})
    except Exception:
        pass
    
    # For all other tool calls, pass to the FastMCP handler
    return await mcp.handle_http_request(request)

async def home(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App (The Routing Bridge)
# This setup ensures the 'lifespan' (startup) signals reach the MCP engine
app = Starlette(
    routes=[
        Route("/", endpoint=home, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
        Mount("/mcp", app=mcp.http_app(stateless_http=True))
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    # lifespan="on" is mandatory to wake up the MCP task groups
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
