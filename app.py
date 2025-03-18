import streamlit as st
import openai
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
from src.firebase_config import db
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from src.authenticate import login, register, guest_login
from src.chat_bot import initialize_chatbot, chat_interface

st.set_page_config(page_title="Mental Care AI", layout="wide")

st.markdown("""
    <style>
        body { background-color: #121212; color: white; }
        .stButton button { background-color: #1DB954; color: white; border-radius: 10px; }
        .st-tabs [role="tablist"] { justify-content: center; }
    </style>
""", unsafe_allow_html=True)

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)
openai.api_key = st.secrets["OPENAI_API_KEY"]

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
        container = st.container()
        if "user_info" not in st.session_state or not st.session_state.user_info:
            st.session_state.user_info = "No user info available" 
        session_id = f"chat_{st.session_state.username}"
        agent = initialize_chatbot(session_id, container, st.session_state.username, st.session_state.user_info)
        chat_interface(agent, session_id, container)
    else:
        st.warning("🔑 Vui lòng đăng nhập để sử dụng chatbot.")

with tab3:
    if st.session_state.logged_in:
        st.header("📊 Theo dõi thông tin sức khỏe của bạn")

        def save_score_in_subcollection(username, score, content, total_guess):
            """Save score in the user's subcollection of scores."""
            user_ref = db.collection("user_scores").document(username)
            
            # Save score as a new document in the score_history subcollection
            user_ref.collection("score_history").add({
                "score": score,
                "time": datetime.now(timezone.utc),  # Timestamp in UTC
                "content": content if content else "Không có mô tả",
                "total_guess": total_guess if total_guess else "Không có dữ liệu"
            })

        def load_scores_from_firebase(username):
            """Retrieve user scores from Firestore."""
            scores_ref = db.collection("user_scores").document(username).collection("score_history")
            docs = scores_ref.stream()
            data = [doc.to_dict() for doc in docs]
            return pd.DataFrame(data) if data else pd.DataFrame(columns=["score", "time", "content", "total_guess"])

        def score_to_numeric(score):
            """Convert textual scores to numeric for visualization."""
            return {"kém": 1, "trung bình": 2, "khá": 3, "tốt": 4}.get(score.lower(), 0)

        def plot_scores(df):
            """Plot user's mental health scores over time."""
            df['time'] = pd.to_datetime(df['time'])
            df['score_num'] = df['score'].apply(score_to_numeric)

            color_map = {'kém': 'red', 'trung bình': 'orange', 'khá': 'yellow', 'tốt': 'green'}
            df['color'] = df['score'].map(color_map)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['time'], y=df['score_num'], mode='lines+markers',
                                    marker=dict(size=24, color=df['color']), text=df['score'], line=dict(width=2)))
            fig.update_layout(xaxis_title='Ngày', yaxis_title='Score',
                            yaxis=dict(tickvals=[1, 2, 3, 4], ticktext=['kém', 'trung bình', 'khá', 'tốt']),
                            hovermode='x unified')

            st.plotly_chart(fig)

        # Load user scores from Firebase
        df = load_scores_from_firebase(st.session_state.username)

        if not df.empty:
            st.markdown("## 📊 Biểu đồ sức khỏe tinh thần của bạn")
            plot_scores(df)

            st.markdown("## 📆 Truy xuất thông tin sức khỏe theo ngày")
            selected_date = st.date_input("📅 Chọn ngày", datetime.now().date())
            selected_date = pd.to_datetime(selected_date)

            if not df.empty:
                filtered_df = df[df["time"].dt.date == selected_date.date()]
                if not filtered_df.empty:
                    st.write(f"📅 **Thông tin ngày {selected_date.date()}**")
                    for _, row in filtered_df.iterrows():
                        st.markdown(f"**🕒 Thời gian:** {row['time']}  \n"
                                    f"**📈 Điểm:** {row['score']}  \n"
                                    f"**📜 Nội dung:** {row['content']}  \n"
                                    f"**📊 Tổng dự đoán:** {row['total_guess']}  \n")
                else:
                    st.write(f"❌ Không có dữ liệu cho ngày {selected_date.date()}")

            st.markdown("## 📋 Bảng dữ liệu chi tiết")
            st.table(df)
        else:
            st.warning("❌ Không có dữ liệu để hiển thị.")
    else:
        st.warning("🔑 Vui lòng đăng nhập để xem thông tin sức khỏe.")


if __name__ == "__main__":
    pass  
