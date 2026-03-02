import os
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request

# 1. Initialize FastMCP with stateless mode for AWS
mcp = FastMCP("KnowledgeBase", stateless_http=True)

# 2. Add the Health Check for App Runner
@mcp.custom_route("GET", "/")
async def health_check(request):
    return JSONResponse({"status": "online"})

# 3. THE HANDSHAKE FIX: Catch the AWS 'initialized' ping
# This intercepts the POST to /mcp before it hits the tool logic
@mcp.custom_route("POST", "/mcp")
async def handle_mcp_post(request: Request):
    try:
        body = await request.json()
        # If AWS sends the initialization ping, we MUST reply with 'ok'
        if body.get("method") == "notifications/initialized":
            return JSONResponse({
                "jsonrpc": "2.0", 
                "result": "ok", 
                "id": body.get("id")
            })
    except Exception:
        pass
    
    # For all other calls (actual tools), let FastMCP handle it
    return await mcp.handle_http_request(request)

# --- YOUR TOOLS ---
@mcp.tool()
def hello_world() -> str:
    """A test tool to verify the connection is alive."""
    return "Success! The MCP server and Bedrock Gateway are now talking."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Use mcp.run to handle the background task groups correctly
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
