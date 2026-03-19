import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # Recommended for App Runner/Quick Suite talk

app = Flask(__name__)
CORS(app) # Allows Quick Suite to reach the endpoint without browser blocks

# --- MCP TOOLS LOGIC ---
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

# --- ROUTES ---

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "MCP Knowledge Server",
        "mcp_endpoint": "/mcp"
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    request_id = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}), 400
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        # 1. INITIALIZE: The first thing Quick Suite will send
        if method == "initialize":
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "logging": {}
                    },
                    "serverInfo": {"name": "KnowledgeBase", "version": "1.0.0"}
                }
            })

        # 2. LIST TOOLS: Quick Suite asks what you can do
        elif method == "tools/list":
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": list(TOOLS.values())}
            })
        
        # 3. CALL TOOLS: Execution logic
        elif method == "tools/call":
            tool_name = params.get("name")
            
            if tool_name == "hello_world":
                result_data = hello_world()
            elif tool_name == "get_server_info":
                result_data = get_server_info()
            else:
                return jsonify({
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                }), 404
            
            # MCP requires result to be wrapped in a 'content' list
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_data) if isinstance(result_data, (dict, list)) else str(result_data)
                        }
                    ],
                    "isError": False
                }
            })
        
        # 4. NOTIFICATIONS: Handle 'initialized' or others silently
        elif method.startswith("notifications/"):
            return '', 204

        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }), 404
    
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": str(e)}
        }), 500

if __name__ == "__main__":
    # App Runner provides the PORT variable
    port = int(os.environ.get("PORT", 8080))
    # Must use 0.0.0.0 for App Runner to route traffic to the container
    app.run(host="0.0.0.0", port=port)
