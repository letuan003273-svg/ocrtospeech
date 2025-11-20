import streamlit as st
import google.generativeai as genai

# Cấu hình API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.write("### Danh sách các Model hiện có:")

# Liệt kê tất cả model
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            st.code(m.name) # Nó sẽ in ra dạng: models/gemini-1.5-pro
except Exception as e:
    st.error(f"Lỗi: {e}")
