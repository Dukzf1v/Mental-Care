import os
import json
from datetime import datetime
import streamlit as st
from llama_index.core import load_index_from_storage
from llama_index.core import StorageContext
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.tools import FunctionTool
from src.paths import INDEX_STORAGE, CONVERSATION_FILE, SCORES_FILE
from src.prompts import CUSTORM_AGENT_SYSTEM_TEMPLATE

user_avatar = "data/images/user_avatar.jpg"
professor_avatar = "data/images/professor_avatar.jpg"

def load_chat_store():
    if os.path.exists(CONVERSATION_FILE) and os.path.getsize(CONVERSATION_FILE) > 0:
        try:
            chat_store = SimpleChatStore.from_persist_path(CONVERSATION_FILE)
        except json.JSONDecodeError:
            chat_store = SimpleChatStore()
    else:
        chat_store = SimpleChatStore()
    return chat_store

def display_messages(chat_store, container, key):
    with container:
        for message in chat_store.get_messages(key=key):
            if message.role == "user":
                with st.chat_message(message.role, avatar=user_avatar):
                    st.markdown(message.content)
            elif message.role == "assistant" and message.content != None:
                with st.chat_message(message.role, avatar=professor_avatar):
                    st.markdown(message.content)
def save_score(score, content, total_guess, username):

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "username": username,
            "Time": current_time,
            "Score": score,
            "Content": content,
            "Total guess": total_guess
        }

        try:
            with open(SCORES_FILE, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []

        data.append(new_entry)

        with open(SCORES_FILE, "w") as f:
            json.dump(data, f, indent=4)
    
def initialize_chatbot(chat_store, container, username, user_info):
    memory = ChatMemoryBuffer.from_defaults(
        token_limit=3000, 
        chat_store=chat_store, 
        chat_store_key= username
    )  
    storage_context = StorageContext.from_defaults(
        persist_dir=INDEX_STORAGE
    )
    index = load_index_from_storage(
        storage_context, index_id="vector"
    )
    dsm5_engine = index.as_query_engine(
        similarity_top_k=3,
    )
    dsm5_tool= QueryEngineTool(
        query_engine=dsm5_engine, 
        metadata=ToolMetadata(
            name="dsm5",
            description=(
                f"Cung cấp các thông tin liên quan đến các bệnh "
                f"tâm thần theo tiêu chuẩn DSM5. Sử dụng câu hỏi văn bản thuần túy chi tiết làm đầu vào cho công cụ"
            ),
        )
    )   
    save_tool = FunctionTool.from_defaults(fn=save_score)
    agent = OpenAIAgent.from_tools(
        tools=[dsm5_tool, save_tool], 
        memory=memory,
        system_prompt=CUSTORM_AGENT_SYSTEM_TEMPLATE.format(user_info=user_info)
    )
    display_messages(chat_store, container, key=username)
    return agent

def chat_interface(agent, chat_store, container):  
    if not os.path.exists(CONVERSATION_FILE) or os.path.getsize(CONVERSATION_FILE) == 0:
        with container:
            with st.chat_message(name="assistant", avatar=professor_avatar):
                st.markdown("Chào bạn, mình sẽ giúp bạn chăm sóc sức khỏe tinh thần. Hãy nói chuyện với mình để bắt đầu.")
    prompt = st.chat_input("Viết tin nhắn tại đây ạ...")
    if prompt:
        with container:
            with st.chat_message(name="user", avatar=user_avatar):
                st.markdown(prompt)
            response = str(agent.chat(prompt))
            with st.chat_message(name="assistant", avatar=professor_avatar):
                st.markdown(response)
        chat_store.persist(CONVERSATION_FILE)