import streamlit as st
import boto3
import uuid
import json

# 1. Page Config
st.set_page_config(page_title="MCP Knowledge Assistant", page_icon="📚")
st.title("📚 Knowledge Assistant")

# 2. Connection Setup
# Ensure 'bedrock-agentcore' is used as the service name
client = boto3.client("bedrock-agentcore", region_name="us-east-1")

GATEWAY_ID = "gateway-quick-start-371cd1-z83wxas8vh"
GATEWAY_ARN = f"arn:aws:bedrock-agentcore:us-east-1:273107214895:gateway/{GATEWAY_ID}"

if "messages" not in st.session_state:
    st.session_state.messages = []

# FIX: Session ID must be at least 33 characters for AgentCore
if "session_id" not in st.session_state:
    st.session_state.session_id = f"mcp-session-{uuid.uuid4().hex}-runtime-active"

# 3. Display Chat
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. Handle Input
if prompt := st.chat_input("Ask a question about your knowledge base..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Talking to AI Gateway..."):
        try:
            # We omit 'qualifier' to let AWS pick the default/latest synced runtime automatically
            response = client.invoke_agent_runtime(
                agentRuntimeArn=GATEWAY_ARN,
                runtimeSessionId=st.session_state.session_id,
                payload=json.dumps({"prompt": prompt}).encode('utf-8'),
                contentType='application/json',
                accept='application/json'
            )

            # Read the streaming body response
            response_body = response['response'].read().decode('utf-8')
            response_json = json.loads(response_body)
            
            # Extract the text answer
            answer = response_json.get("result", response_json.get("content", "No answer returned."))

        except Exception as e:
            answer = f"⚠️ Connection Error: {str(e)}"

    st.chat_message("assistant").write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
