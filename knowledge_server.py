import os
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    return "The handshake is finally complete!"

mcp_app = mcp.http_app(stateless_http=True)

async def handle_mcp_post(request):
    body = await request.body()

    # Intercept AWS invalid pre-init notification
    if b'"method":"notifications/initialized"' in body:
        return Response(status_code=200)

    return await mcp_app(request.scope, request.receive, request.send)

async def health_check(request):
    return JSONResponse({"status": "online"})

app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp_post, methods=["POST"]),
    ],
    lifespan=mcp_app.lifespan
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
