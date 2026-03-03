import os
import json
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.requests import Request

# ---------------------------------------------------
# 1. Initialize FastMCP
# ---------------------------------------------------

mcp = FastMCP("KnowledgeBase", stateless_http=True)

@mcp.tool()
def hello_world() -> str:
    """Verifies MCP connection."""
    return "Sync successful! Tools are active."


# ---------------------------------------------------
# 2. MCP Universal Handler (AgentCore Compatible)
# ---------------------------------------------------

async def handle_mcp(request: Request):
    print(f"{request.method} {request.url.path}")

    # ✅ Allow GET (AgentCore health probe)
    if request.method == "GET":
        return JSONResponse({"status": "mcp_active", "transport": "http"})

    # ✅ Read request body ONCE
    body_bytes = await request.body()

    # ✅ Handle AWS AgentCore initialization notification
    if body_bytes:
        try:
            payload = json.loads(body_bytes)

            if payload.get("method") == "notifications/initialized":
                print("Handled AWS initialization notification")
                return Response(status_code=200, content="")

        except Exception:
            pass

    # ---------------------------------------------------
    # IMPORTANT:
    # We must recreate the receive() function because
    # reading request.body() consumes the stream.
    # ---------------------------------------------------

    async def receive():
        return {
            "type": "http.request",
            "body": body_bytes,
            "more_body": False,
        }

    # Forward request to FastMCP ASGI app
    mcp_app = mcp.http_app(stateless_http=True)

    response = Response(status_code=500)

    async def send(message):
        nonlocal response

        if message["type"] == "http.response.start":
            response.status_code = message["status"]
            response.raw_headers = message.get("headers", [])

        elif message["type"] == "http.response.body":
            response.body = message.get("body", b"")

    await mcp_app(request.scope, receive, send)

    return response


# ---------------------------------------------------
# 3. Health Check Endpoint
# ---------------------------------------------------

async def health_check(request):
    return JSONResponse({"status": "online"})


# ---------------------------------------------------
# 4. Starlette App
# ---------------------------------------------------

app = Starlette(
    routes=[
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=handle_mcp, methods=["GET", "POST", "OPTIONS"]),
        Route("/mcp/", endpoint=handle_mcp, methods=["GET", "POST", "OPTIONS"]),
    ],
    lifespan=mcp.http_app(stateless_http=True).lifespan,
)


# ---------------------------------------------------
# 5. Run Server (App Runner compatible)
# ---------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        lifespan="on"   # REQUIRED for FastMCP tool activation
    )
