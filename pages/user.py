import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from src.global_settings import SCORES_FILE
import plotly.graph_objects as go

st.set_page_config(layout="wide")

def load_scores(file, specific_username):
    if os.path.exists(file) and os.path.getsize(file) > 0:
        with open(file, 'r') as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        new_df = df[df["username"] == specific_username]
        return new_df
    else:
        return pd.DataFrame(columns=["username", "Time", "Score", "Content", "Total guess"])

def score_to_numeric(score):
    score = score.lower()
    if score == "kém":
        return 1
    elif score == "trung bình":
        return 2
    elif score == "khá":
        return 3
    elif score == "tốt":
        return 4

def plot_scores(df):

    df['Time'] = pd.to_datetime(df['Time'])

    recent_date = df['Time'].max()
    start_date = recent_date - pd.Timedelta(days=6)
    df_filtered = df[(df['Time'] >= start_date) & (df['Time'] <= recent_date)]

    df_filtered = df_filtered.sort_values(by='Time')

    color_map = {
        'kém': 'red',
        'trung bình': 'orange',
        'khá': 'yellow',
        'tốt': 'green'
    }

    df_filtered['color'] = df_filtered['Score'].map(color_map)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_filtered['Time'],
        y=df_filtered['Score_num'],
        mode='lines+markers',
        marker=dict(size=24, color=df_filtered['color']),
        text=df_filtered['Score'],
        line=dict(width=2)
    ))

    fig.update_layout(
        xaxis_title='Ngày',
        yaxis_title='Score',
        xaxis=dict(tickformat='%Y-%m-%d'),
        yaxis=dict(tickvals=[1, 2, 3, 4], ticktext=['kém', 'trung bình', 'khá', 'tốt']),
        hovermode='x unified'
    )

    st.plotly_chart(fig)
    
def main():

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if st.session_state.logged_in:

        st.markdown('# Theo dõi thông tin sức khỏe của bạn')

        df = load_scores(SCORES_FILE, st.session_state.username)
        if not df.empty:
            df["Time"] = pd.to_datetime(df["Time"])
            df["Score_num"] = df["Score"].apply(score_to_numeric)
            df["Score"] = df["Score"].str.lower()

            st.markdown("## Biểu đồ sức khỏe tinh thần 7 ngày qua của bạn")
            plot_scores(df)

        st.markdown("## Truy xuất thông tin sức khỏe tinh thần theo ngày")
        date = st.date_input("Chọn ngày", datetime.now().date())
        selected_date = pd.to_datetime(date)
        if not df.empty:
            filtered_df = df[df["Time"].dt.date == selected_date.date()]

            if not filtered_df.empty:
                st.write(f"Thông tin ngày {selected_date.date()}:")
                for index, row in filtered_df.iterrows():
                    st.markdown(f"""
                    **Thời gian:** {row['Time']}  
                    **Điểm:** {row['Score']}  
                    **Nội dung:** {row['Content']}  
                    **Tổng dự đoán:** {row['Total guess']}  
                    """)
            else:
                st.write(f"Không có dữ liệu cho ngày {selected_date.date()}")
        st.markdown("## Bảng dữ liệu chi tiết")
        st.table(df)    

if __name__ == "__main__":
    main()