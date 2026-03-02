import os
from fastmcp import FastMCP
from starlette.responses import JSONResponse

# 1. Initialize FastMCP with the AWS-required flag
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# 2. Add the Health Check for App Runner
@mcp.custom_route("GET", "/")
def health_check():
    return {"status": "online"}

# 3. THE FIX: Explicitly handle the "notifications/initialized" method
# This prevents the -32601 "Method not found" error during Gateway Sync
@mcp.custom_route("POST", "/mcp")
async def handle_mcp_post(request):
    try:
        body = await request.json()
        if body.get("method") == "notifications/initialized":
            # Return a standard JSON-RPC success response
            return JSONResponse({"jsonrpc": "2.0", "result": "ok", "id": body.get("id")})
    except:
        pass
    
    # Otherwise, let the normal MCP handler take over
    return await mcp.handle_http_request(request)

# --- YOUR TOOLS ---
@mcp.tool()
def hello_world() -> str:
    """Simple test tool."""
    return "The MCP server is connected and working!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Using the built-in run method
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
