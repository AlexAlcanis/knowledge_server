import streamlit as st
import boto3
import uuid

# 1. Setup the Page
st.set_page_config(page_title="Knowledge AI", page_icon="📚")
st.title("📚 Knowledge Base Assistant")

# 2. Connect to Bedrock
# Ensure you have your AWS credentials set in your environment
client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

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

    # Call your Bedrock Agent
    response = client.invoke_agent(
        agentId='YOUR_AGENT_ID', 
        agentAliasId='YOUR_ALIAS_ID',
        sessionId=st.session_state.session_id,
        inputText=prompt,
    )

    # Stream the answer back
    answer = ""
    for event in response.get("completion"):
        answer += event.get("chunk").get("bytes").decode()
    
    st.chat_message("assistant").write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
