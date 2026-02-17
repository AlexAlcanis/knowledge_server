import streamlit as st
import boto3
import uuid
import json

# 1. Page Config
st.set_page_config(page_title="MCP Knowledge Assistant", page_icon="📚")
st.title("📚 MCP Knowledge Assistant")

# 2. Connection Setup
# Streamlit Cloud needs 'boto3>=1.35.0' in requirements.txt
client = boto3.client("bedrock-agentcore", region_name="us-east-1")

GATEWAY_ID = "gateway-quick-start-371cd1-z83wxas8vh"
GATEWAY_ARN = f"arn:aws:bedrock-agentcore:us-east-1:273107214895:gateway/{GATEWAY_ID}"

if "messages" not in st.session_state:
    st.session_state.messages = []

# FIX: Session ID must be at least 33 characters for AgentCore
if "session_id" not in st.session_state:
    st.session_state.session_id = f"mcp-runtime-session-{uuid.uuid4().hex}"

# 3. Display Chat History
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. Handle Chat Input
if prompt := st.chat_input("Ask about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Invoking Gateway..."):
        try:
            # We omit 'qualifier' because the SDK defaults to 'DEFAULT'.
            # The 'DEFAULT' endpoint is created ONLY after a successful SYNC in the console.
            response = client.invoke_agent_runtime(
                agentRuntimeArn=GATEWAY_ARN,
                runtimeSessionId=st.session_state.session_id,
                payload=json.dumps({"prompt": prompt}).encode('utf-8'),
                contentType='application/json',
                accept='application/json'
            )

            # Read the 'response' key (StreamingBody)
            response_body = response['response'].read().decode('utf-8')
            response_json = json.loads(response_body)
            
            # Extract the text answer
            # AgentCore Gateway typically returns text in the 'result' key
            answer = response_json.get("result", response_json.get("content", "No answer content found."))

        except Exception as e:
            answer = f"⚠️ Error: {str(e)}"

    st.chat_message("assistant").write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
