import os
import json
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request

# 1. Initialize FastMCP with stateless mode for AWS
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# 2. Health Check for App Runner
@mcp.custom_route("GET", "/")
async def health_check(request):
    return JSONResponse({"status": "online", "mcp_endpoint": "/mcp"})

# 3. THE HANDSHAKE FIX: Catch the AWS "initialized" ping
@mcp.custom_route("POST", "/mcp")
async def handle_mcp_handshake(request: Request):
    try:
        body = await request.json()
        # If AWS sends the initialization ping, reply immediately with success
        if body.get("method") == "notifications/initialized":
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": "ok",
                "id": body.get("id")
            })
    except Exception:
        pass
    
    # Otherwise, pass the request to the standard MCP handler
    return await mcp.handle_http_request(request)

# --- YOUR TOOLS ---
@mcp.tool()
def read_knowledge_base() -> str:
    """Returns a test message to verify the tool is visible to Bedrock."""
    return "The Knowledge Base is connected and tools are active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # mcp.run handles the ASGI lifespan automatically
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
