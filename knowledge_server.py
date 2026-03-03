import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.responses import JSONResponse

# -----------------------------------
# 1. Create MCP Server
# -----------------------------------

mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    return "Sync successful! Tools are active."

# -----------------------------------
# 2. Health Endpoint
# -----------------------------------

async def health_check(request):
    return JSONResponse({"status": "online"})

# -----------------------------------
# 3. Mount MCP directly (CRITICAL)
# -----------------------------------

app = Starlette(
    routes=[
        Mount("/mcp", app=mcp.http_app(stateless_http=True)),
        Mount("/", app=Starlette(routes=[])),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan,
)

# Add root health route separately
app.add_route("/", health_check, methods=["GET"])

# -----------------------------------
# 4. Run
# -----------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
