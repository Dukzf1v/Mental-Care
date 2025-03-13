import streamlit as st
import openai
import json
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from src.authenticate import login, register, guest_login
from src.conversation_engine import initialize_chatbot, chat_interface, load_chat_store
from src.global_settings import SCORES_FILE

st.set_page_config(page_title="Mental Care AI", layout="wide")

st.markdown("""
    <style>
        body { background-color: #121212; color: white; }
        .stButton button { background-color: #1DB954; color: white; border-radius: 10px; }
        .st-tabs [role="tablist"] { justify-content: center; } /* Center tabs */
    </style>
""", unsafe_allow_html=True)

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)
openai.api_key = st.secrets.openai.OPENAI_API_KEY

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

tab1, tab2, tab3 = st.tabs(["🏠 Home", "💬 Chat", "📊 User Info"])

with tab1:
    st.header("🧠 Mental Care AI - Welcome!")

    if not st.session_state.logged_in:
        with st.expander('MENTAL HEALTH - Login Required', expanded=True):
            login_tab, create_tab, guest_tab = st.tabs(["🔑 Đăng nhập", "🆕 Tạo tài khoản", "👥 Khách"])
            with create_tab:
                register()
            with login_tab:
                login()
            with guest_tab:
                guest_login()
    else:
        st.success(f'Chào mừng {st.session_state.username}, hãy khám phá các tính năng của ứng dụng!', icon="🎉")

with tab2:
    if st.session_state.logged_in:
        st.header("💬 AI Mental Health Chatbot")
        chat_store = load_chat_store()
        container = st.container()
        agent = initialize_chatbot(chat_store, container, st.session_state.username, st.session_state.user_info)
        chat_interface(agent, chat_store, container)
    else:
        st.warning("🔑 Vui lòng đăng nhập để sử dụng chatbot.")

with tab3:
    if st.session_state.logged_in:
        st.header("📊 Theo dõi thông tin sức khỏe của bạn")

        def load_scores(file, specific_username):
            if os.path.exists(file) and os.path.getsize(file) > 0:
                with open(file, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                return df[df["username"] == specific_username]
            else:
                return pd.DataFrame(columns=["username", "Time", "Score", "Content", "Total guess"])

        def score_to_numeric(score):
            return {"kém": 1, "trung bình": 2, "khá": 3, "tốt": 4}.get(score.lower(), 0)

        def plot_scores(df):
            df['Time'] = pd.to_datetime(df['Time'])
            df['Score_num'] = df['Score'].apply(score_to_numeric)

            color_map = {'kém': 'red', 'trung bình': 'orange', 'khá': 'yellow', 'tốt': 'green'}
            df['color'] = df['Score'].map(color_map)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Time'], y=df['Score_num'], mode='lines+markers',
                                     marker=dict(size=24, color=df['color']), text=df['Score'], line=dict(width=2)))
            fig.update_layout(xaxis_title='Ngày', yaxis_title='Score',
                              yaxis=dict(tickvals=[1, 2, 3, 4], ticktext=['kém', 'trung bình', 'khá', 'tốt']),
                              hovermode='x unified')

            st.plotly_chart(fig)

        df = load_scores(SCORES_FILE, st.session_state.username)
        if not df.empty:
            st.markdown("## 📊 Biểu đồ sức khỏe tinh thần 7 ngày qua của bạn")
            plot_scores(df)

        st.markdown("## 📆 Truy xuất thông tin sức khỏe theo ngày")
        selected_date = st.date_input("📅 Chọn ngày", datetime.now().date())
        selected_date = pd.to_datetime(selected_date)

        if not df.empty:
            filtered_df = df[df["Time"].dt.date == selected_date.date()]
            if not filtered_df.empty:
                st.write(f"📅 **Thông tin ngày {selected_date.date()}**")
                for _, row in filtered_df.iterrows():
                    st.markdown(f"**🕒 Thời gian:** {row['Time']}  \n"
                                f"**📈 Điểm:** {row['Score']}  \n"
                                f"**📜 Nội dung:** {row['Content']}  \n"
                                f"**📊 Tổng dự đoán:** {row['Total guess']}  \n")
            else:
                st.write(f"❌ Không có dữ liệu cho ngày {selected_date.date()}")

        st.markdown("## 📋 Bảng dữ liệu chi tiết")
        st.table(df)
    else:
        st.warning("🔑 Vui lòng đăng nhập để xem thông tin sức khỏe.")

if __name__ == "__main__":
    pass  
