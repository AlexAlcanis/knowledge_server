import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# MCP tools
def hello_world():
    return "The MCP server is connected and working!"

def get_server_info():
    return {
        "name": "KnowledgeBase MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools_available": 2
    }

TOOLS = {
    "hello_world": {
        "name": "hello_world",
        "description": "A simple test tool to verify MCP is working",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    "get_server_info": {
        "name": "get_server_info",
        "description": "Get information about the MCP server",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    }
}

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "MCP Knowledge Server",
        "mcp_endpoint": "/mcp",
        "tools": len(TOOLS)
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None
            }), 400
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        if method == "tools/list":
            return jsonify({
                "jsonrpc": "2.0",
                "result": {"tools": list(TOOLS.values())},
                "id": request_id
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            if tool_name == "hello_world":
                result = hello_world()
            elif tool_name == "get_server_info":
                result = get_server_info()
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                    "id": request_id
                }), 404
            
            return jsonify({
                "jsonrpc": "2.0",
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result) if isinstance(result, dict) else str(result)
                    }]
                },
                "id": request_id
            })
        
        elif method == "initialize":
            return jsonify({
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "KnowledgeBase", "version": "1.0.0"}
                },
                "id": request_id
            })
        
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }), 404
    
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": request_id if 'request_id' in locals() else None
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting MCP Server on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
