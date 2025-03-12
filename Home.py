import streamlit as st
from src.authenticate import login, register, guest_login

def main():
    
    # Giao diện đăng nhập
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.expander('MENTAL HEALTH', expanded=True):
            login_tab, create_tab, guest_tab = st.tabs(
                [
                    "Đăng nhập",
                    "Tạo tài khoản",
                    "Khách"
                ]
            )
            with create_tab:
                register()
            with login_tab:
                login()
            with guest_tab:
                guest_login()
    else:
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Nói chuyện với chuyên gia tâm lý AI"):
                st.switch_page("pages/chat.py")
        with col2:
            if st.button("Theo dõi thông tin sức khỏe của bạn"):
                st.switch_page("pages/user.py")
        st.success(f'Chào mừng {st.session_state.username}, hãy khám phá các tính năng của ứng dụng chăm sóc sức khỏe tinh thần nhé!', icon="🎉")
if __name__ == "__main__":
    main()