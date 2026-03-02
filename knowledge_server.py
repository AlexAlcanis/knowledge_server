import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# --- TOOLS ---
@mcp.tool()
def query_knowledge_base(question: str) -> str:
    """Answers questions using the connected knowledge base."""
    return f"Processed query: {question}. The connection is stable!"

# 2. THE HANDSHAKE FIX (Option 2 from your info)
async def handle_mcp_post(request):
    try:
        body = await request.json()
        
        # Intercept the specific lifecycle notification that AWS sends
        # If method is notifications/initialized, we MUST return a 200/202 
        # and NOT an error -32601.
        if body.get("method") == "notifications/initialized":
            return Response(status_code=200) # Accept it and return nothing
            
    except Exception:
        pass
    
    # For all other methods (initialize, tools/list, tools/call), 
    # let the MCP engine handle it.
    return await mcp.handle_http_request(request)

async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. Create the Starlette App
app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    # Important: This initializes the MCP task groups for tool execution
    lifespan=mcp.http_app(stateless_http=True).lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # lifespan="on" is critical for the MCP lifecycle
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
