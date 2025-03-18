import streamlit as st
import hashlib
from src.firebase_config import db

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def load_user(username):
    user_ref = db.collection("users").document(username)
    doc = user_ref.get()
    return doc.to_dict() if doc.exists else None

def save_user(username, user_data):
    user_ref = db.collection("users").document(username)
    user_ref.set(user_data)

def register():
    with st.form(key="register"):
        st.subheader('Register')
        username = st.text_input('Tên tài khoản')
        email = st.text_input('Email')
        name = st.text_input('Họ tên')
        age = st.number_input('Tuổi', min_value=5, max_value=100)
        gender = st.selectbox('Giới tính', ['Nam', 'Nữ', 'Khác'])
        password = st.text_input('Mật khẩu', type='password')
        confirm_password = st.text_input('Xác nhận mật khẩu', type='password')

        if st.form_submit_button('Đăng ký'):
            if not username or not password:
                st.error('Bạn cần nhập tên tài khoản và mật khẩu!')
            elif password != confirm_password:
                st.error('Mật khẩu không khớp!')
            else:
                existing_user = load_user(username)
                if existing_user:
                    st.error('Tên tài khoản đã tồn tại!')
                else:
                    hashed_password = hash_password(password)
                    user_data = {
                        'email': email,
                        'name': name,
                        'age': age,
                        'gender': gender,
                        'password': hashed_password
                    }
                    save_user(username, user_data)
                    st.session_state.username = username
                    st.session_state.logged_in = True
                    st.session_state.user_info = f"username:{username}, " + ", ".join([f"{k}:{v}" for k, v in user_data.items() if k != 'password'])
                    st.success("Đăng ký thành công! Vui lòng đăng nhập.")
                    st.rerun()

def login():
    with st.form(key="login"):
        username = st.text_input('Tên đăng nhập')
        password = st.text_input('Mật khẩu', type='password')

        if st.form_submit_button('Đăng nhập'):
            user_data = load_user(username)
            if user_data:
                if verify_password(user_data['password'], password):
                    st.session_state.username = username
                    st.session_state.logged_in = True
                    st.session_state.user_info = f"username:{username}, " + ", ".join([f"{k}:{v}" for k, v in user_data.items() if k != 'password'])
                    st.session_state.messages = []
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error('Mật khẩu không chính xác!')
            else:
                st.error('Tên đăng nhập không tồn tại!')

def guest_login():
    if st.button('Khách đăng nhập'):
        st.session_state.logged_in = True
        st.session_state.username = 'Khách'
        st.session_state.user_info = "username:Khách, Chưa cung cấp thông tin"
        st.success("Bạn đang đăng nhập với tư cách khách.")
        st.rerun()

if __name__ == '__main__':
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.expander('MENTAL HEALTH', expanded=True):
            login_tab, create_tab = st.tabs(["Đăng nhập", "Tạo tài khoản"])
            with create_tab:
                register()
            with login_tab:
                login()
            guest_login()
    else:
        st.write(f"Welcome, {st.session_state.username}!")