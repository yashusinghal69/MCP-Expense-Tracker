import asyncio
import os
from dotenv import load_dotenv
import json
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
import streamlit as st

load_dotenv()
 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  

SERVERS={
#    "Expense Tracker": {
#        "transport": "stdio",
#       "command": "C:\\Users\\yashu\\.local\\bin\\uv.exe",
#       "args": [
#         "run",
#         "--project",
#         "E:\\MCP CampusX",
#         "fastmcp",
#         "run",
#         "E:\\MCP CampusX\\local_server.py"
#       ]
#     },

    'Expense Tracker Proxy': {
        "transport": "streamable_http",    
        'url': "https://mcp-expense-tracker-supabase.fastmcp.app/mcp"
    }    
}

SYSTEM_PROMPT = (
    "You have access to tools. When you choose to call a tool, do not narrate status updates. "
    "After tools run, return only a concise final answer."
)

# One-time init
if "initialized" not in st.session_state:
    # 1) LLM
    st.session_state.llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=GOOGLE_API_KEY,
        temperature=0.7
    )

    # 2) MCP tools
    st.session_state.client = MultiServerMCPClient(SERVERS)
    tools = asyncio.run(st.session_state.client.get_tools())
    st.session_state.tools = tools
    st.session_state.tool_by_name = {t.name: t for t in tools}

    # 3) Bind tools
    st.session_state.llm_with_tools = st.session_state.llm.bind_tools(tools)

    # 4) Conversation state
    st.session_state.history = [SystemMessage(content=SYSTEM_PROMPT)]
    st.session_state.initialized = True


# Render chat history (skip system + tool messages; hide intermediate AI with tool_calls)
for msg in st.session_state.history:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        # Skip assistant messages that contain tool_calls (intermediate “fetching…”)
        if getattr(msg, "tool_calls", None):
            continue
        with st.chat_message("assistant"):
            st.markdown(msg.content)



user_text = st.chat_input("Type a message…")
if user_text:
    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.history.append(HumanMessage(content=user_text))

    # First pass: let the model decide whether to call tools
    first = asyncio.run(st.session_state.llm_with_tools.ainvoke(st.session_state.history))
    tool_calls = getattr(first, "tool_calls", None)

    if not tool_calls:
        # No tools → show & store assistant reply
        with st.chat_message("assistant"):
            st.markdown(first.content or "")
        st.session_state.history.append(first)
    else:
        # ── IMPORTANT ORDER ──
        # 1) Append assistant message WITH tool_calls (do NOT render)
        st.session_state.history.append(first)

        # 2) Execute requested tools and append ToolMessages (do NOT render)
        tool_msgs = []
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            tool = st.session_state.tool_by_name[name]
            res = asyncio.run(tool.ainvoke(args))
            tool_msgs.append(ToolMessage(tool_call_id=tc["id"], content=json.dumps(res)))

        st.session_state.history.extend(tool_msgs)

        # 3) Final assistant reply using tool outputs → render & store
        final = asyncio.run(st.session_state.llm.ainvoke(st.session_state.history))
        with st.chat_message("assistant"):
            st.markdown(final.content or "")
        st.session_state.history.append(AIMessage(content=final.content or ""))


# async def main():

#     # Initialize MCP client and get tools
#     client = MultiServerMCPClient(SERVERS)
#     tools = await client.get_tools()
    
#     named_tools = {tool.name: tool for tool in tools}
    
#     print("Available Tools:", list(named_tools.keys()))

#     llm = ChatGoogleGenerativeAI(
#         model="gemini-2.5-flash", 
#         google_api_key=GOOGLE_API_KEY,
#         temperature=0.7
#     )
    
#     llm_with_tools = llm.bind_tools(tools)
    
#     query = "please list all expenses in the Food category using the tool."
    
#     # Invoke the model
#     response = await llm_with_tools.ainvoke(query)
 

#     if not getattr(response, 'tool_calls', None):
#         print("Response:", response.content)
#         return 
    
#     tools_messages=[]

#     for tc in response.tool_calls:
         
#         selected_tools = tc['name']
#         selected_tools_args = tc.get('args') or {}
#         selected_tools_id = tc['id']
        
     
#         tool_result = await named_tools[selected_tools].ainvoke(selected_tools_args)
    
        
#         tools_messages.append(ToolMessage( content=json.dumps(tool_result),tool_call_id=selected_tools_id))


#     final_response = await llm.ainvoke([HumanMessage(content=query),response,*tools_messages])   

#     print(f"\n=== Final Response ===")
#     print(f"Content: {final_response.content}")

# if __name__ == "__main__":
#     asyncio.run(main())    