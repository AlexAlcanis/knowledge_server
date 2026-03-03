import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.responses import JSONResponse

mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    return "Sync successful! Tools are active."

async def health_check(request):
    return JSONResponse({"status": "online"})

app = Starlette(
    routes=[
        Mount("/mcp", app=mcp.http_app(stateless_http=True)),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan,
)

app.add_route("/", health_check, methods=["GET"])
