from datetime import datetime, timezone
import streamlit as st
from src.firebase_config import db
from llama_index.core import load_index_from_storage
from llama_index.core import StorageContext
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.memory.chat_memory_buffer import ChatMessage
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.tools import FunctionTool
from src.paths import INDEX_STORAGE
from src.prompts import CUSTORM_AGENT_SYSTEM_TEMPLATE

REDIS_URL = "rediss://default:AYQdAAIjcDEzN2ZlOWEyMDkwNTI0MTJmYjAzZDY0OTJmZjM3NWFmOHAxMA@ruling-ringtail-33821.upstash.io:6379"

chat_store = RedisChatStore(redis_url=REDIS_URL, ttl=7200)  


user_avatar = "data/images/user_avatar.jpg"
professor_avatar = "data/images/professor_avatar.jpg"

def save_chat(session_id, role, content):
    db.collection("chats").document(session_id).collection("messages").add({
        'role': role,
        'content': content,
        'timestamp': datetime.utcnow()
    })

def get_chat(session_id):
    messages_ref = db.collection("chats").document(session_id).collection("messages")
    messages = messages_ref.order_by("timestamp").stream()
    return [{"role": msg.to_dict()["role"], "content": msg.to_dict()["content"]} for msg in messages]

def save_score(username, score, content, total_guess):
    user_ref = db.collection("user_scores").document(username)
    
    user_ref.collection("score_history").add({
        "score": score,
        "time": datetime.now(timezone.utc),
        "content": content if content else "Không có mô tả",
        "total_guess": total_guess if total_guess else "Không có dữ liệu"
    })

def get_score(username):
    user_ref = db.collection("user_scores").document(username)
    doc = user_ref.get()
    return doc.to_dict()["score"] if doc.exists else 0

def display_messages(session_id, container):
    messages = get_chat(session_id)
    with container:
        for message in messages:
            if message["role"] == "user":
                with st.chat_message(message["role"], avatar=user_avatar):
                    st.markdown(message["content"])
            elif message["role"] == "assistant" and message["content"] is not None:
                with st.chat_message(message["role"], avatar=professor_avatar):
                    st.markdown(message["content"])

def initialize_chatbot(session_id, container, username, user_info):

    memory = ChatMemoryBuffer.from_defaults(
        token_limit=3000, 
        chat_store=chat_store, 
        chat_store_key=session_id  
    )  

    storage_context = StorageContext.from_defaults(persist_dir=INDEX_STORAGE)

    index = load_index_from_storage(storage_context, index_id="vector")
    dsm5_engine = index.as_query_engine(similarity_top_k=3)

    dsm5_tool = QueryEngineTool(
        query_engine=dsm5_engine, 
        metadata=ToolMetadata(
            name="dsm5",
            description="Cung cấp các thông tin liên quan đến các bệnh tâm thần theo tiêu chuẩn DSM5."
        ),
    )   
    save_tool = FunctionTool.from_defaults(fn=save_score)

    agent = OpenAIAgent.from_tools(
        tools=[dsm5_tool, save_tool], 
        memory=memory,
        system_prompt=CUSTORM_AGENT_SYSTEM_TEMPLATE.format(user_info=user_info) 
    )

    display_messages(session_id, container)
    return agent

def chat_interface(agent, session_id, container):  
    previous_messages = chat_store.get_messages(session_id) or []

    if not previous_messages:
        with container:
            with st.chat_message(name="assistant", avatar=professor_avatar):
                st.markdown("Chào bạn, mình sẽ giúp bạn chăm sóc sức khỏe tinh thần. Hãy nói chuyện với mình để bắt đầu.")

    prompt = st.chat_input("Viết tin nhắn tại đây")

    if prompt:
        with container:
            with st.chat_message(name="user", avatar=user_avatar):
                st.markdown(prompt)

            # Store message as ChatMessage instead of a dictionary
            user_message = ChatMessage(role="user", content=prompt)
            chat_store.add_message(session_id, user_message)  # ✅ Use ChatMessage

            # Generate response
            response = str(agent.chat(prompt))

            with st.chat_message(name="assistant", avatar=professor_avatar):
                st.markdown(response)

            # Store assistant response as ChatMessage
            assistant_message = ChatMessage(role="assistant", content=response)
            chat_store.add_message(session_id, assistant_message)  # ✅ Use ChatMessage




