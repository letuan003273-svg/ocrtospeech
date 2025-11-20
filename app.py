import streamlit as st
import google.generativeai as genai

# --- Cấu hình trang ---
st.set_page_config(page_title="Chat với Gemini", page_icon="🤖")
st.title("🤖 Trợ lý AI của tôi")

# --- Cấu hình API Key (Lấy từ Secrets của Streamlit) ---
# Đoạn này giúp bảo mật key, không bị lộ ra ngoài
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("Chưa tìm thấy API Key. Vui lòng cấu hình trong Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

# --- Cấu hình Model ---
# Bạn có thể đổi 'gemini-pro' thành model khác nếu muốn
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Giao diện Chat ---
# Tạo lịch sử chat (session state) để AI nhớ ngữ cảnh
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat cũ
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập liệu của người dùng
if prompt := st.chat_input("Hỏi gì đi bạn ơi..."):
    # 1. Hiển thị câu hỏi của người dùng
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Gọi AI trả lời
    try:
        response = model.generate_content(prompt)
        ai_response = response.text

        # 3. Hiển thị câu trả lời của AI
        with st.chat_message("assistant"):
            st.markdown(ai_response)

        # 4. Lưu vào lịch sử
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")
