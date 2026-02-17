import streamlit as st
import boto3
import uuid
import json

# 1. Setup the Page
st.set_page_config(page_title="Knowledge AI", page_icon="📚")
st.title("📚 Knowledge Base Assistant")

# 2. Connect to AgentCore Gateway
# Note the change from 'bedrock-agent-runtime' to 'bedrock-agentcore-runtime'
client = boto3.client("bedrock-agentcore-runtime", region_name="us-east-1")

# Use your Gateway ID from your screenshot
GATEWAY_ID = "gateway-quick-start-371cd1-z83wxas8vh"
# The ARN is required for the new AgentCore SDK
GATEWAY_ARN = f"arn:aws:bedrock-agentcore:us-east-1:273107214895:gateway/{GATEWAY_ID}"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 3. Chat Interface
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Searching knowledge base..."):
        # 4. Call AgentCore Gateway
        # AgentCore uses 'invoke_agent_runtime' and a JSON payload
        response = client.invoke_agent_runtime(
            agentRuntimeArn=GATEWAY_ARN,
            runtimeSessionId=st.session_state.session_id,
            payload=json.dumps({"prompt": prompt}).encode('utf-8'),
            contentType='application/json',
            accept='application/json'
        )

        # 5. Parse the Response
        # AgentCore responses come back in a 'payload' stream
        full_response_bytes = response['payload'].read()
        response_json = json.loads(full_response_bytes.decode('utf-8'))
        
        # Adjusting for common AgentCore output formats
        answer = response_json.get("content", response_json.get("result", "I couldn't find an answer."))

    # 6. Display the result
    st.chat_message("assistant").write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
