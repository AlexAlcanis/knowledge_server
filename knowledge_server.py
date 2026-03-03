import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    return "Sync successful! Tools are active."


async def handle_mcp(request):
    print(f"{request.method} {request.url.path}")

    # AWS initialization notification
    if request.method == "POST":
        body = await request.body()
        if b"notifications/initialized" in body:
            return Response(status_code=200, content="ok")

    # Health probe support
    if request.method == "GET":
        return JSONResponse({"status": "mcp_active"})

    # Forward to MCP ASGI
    mcp_app = mcp.http_app(stateless_http=True)

    response = Response(status_code=500)

    async def send(message):
        nonlocal response
        if message["type"] == "http.response.start":
            response.status_code = message["status"]
            response.raw_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            response.body = message.get("body", b"")

    await mcp_app(request.scope, request.receive, send)
    return response


app = Starlette(
    routes=[
        Route("/", endpoint=lambda r: JSONResponse({"status": "online"})),
        Route("/mcp", endpoint=handle_mcp, methods=["GET", "POST", "OPTIONS"]),
        Route("/mcp/", endpoint=handle_mcp, methods=["GET", "POST", "OPTIONS"]),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
