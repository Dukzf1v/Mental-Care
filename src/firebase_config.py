import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

firebase_json = dict(st.secrets["FIREBASE"])

firebase_json["private_key"] = firebase_json["private_key"].replace("\\n", "\n")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_json)
    firebase_admin.initialize_app(cred)

db = firestore.client()
