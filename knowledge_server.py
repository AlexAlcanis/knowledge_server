import os
from fastmcp import FastMCP
import uvicorn

# 1. Initialize FastMCP
mcp = FastMCP("KnowledgeBase")

# --- TOOL ---
@mcp.tool()
def hello_world() -> str:
    """A simple test tool to verify connection."""
    return "The MCP server is alive and working!"

# 2. Create the App
# stateless_http=True is required for Bedrock Gateway
app = mcp.http_app(stateless_http=True)

if __name__ == "__main__":
    # App Runner sets this to 8080
    port = int(os.environ.get("PORT", 8080))
    
    # We run the mcp_app directly. 
    # Uvicorn will automatically handle the lifespan startup.
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
