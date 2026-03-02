import os
from fastmcp import FastMCP
from starlette.responses import JSONResponse

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# 2. THE FIX: Catch the AWS Handshake manually
@mcp.custom_route("POST", "/mcp")
async def handle_mcp_post(request):
    try:
        body = await request.json()
        # If AWS sends the "initialized" check, give it the 'ok' it wants
        if body.get("method") == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "result": "ok", "id": body.get("id")})
    except Exception:
        pass
    
    # For all other tool calls, use the standard MCP handler
    return await mcp.handle_http_request(request)

# 3. Health check for App Runner
@mcp.custom_route("GET", "/")
def home():
    return {"status": "online"}

# --- YOUR TOOLS ---
@mcp.tool()
def hello_world() -> str:
    """A test tool to verify the connection works."""
    return "Success! The MCP server and Bedrock Gateway are now synchronized."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # mcp.run handles the lifespan/task groups correctly
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
