import streamlit as st
import google.generativeai as genai
from PIL import Image
import edge_tts
import asyncio
import tempfile # Để tạo file tạm thời

# --- 1. Cấu hình trang ---
st.set_page_config(page_title="VisionVoice Pro", page_icon="🎙️", layout="wide")

# --- 2. Cấu hình API Key ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Chưa tìm thấy API Key.")
        st.stop()
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

# --- 3. Hàm xử lý giọng đọc Edge-TTS (MỚI) ---
async def text_to_speech_edge(text, voice_name):
    communicate = edge_tts.Communicate(text, voice_name)
    # Tạo file tạm trong bộ nhớ để lưu âm thanh
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        await communicate.save(tmp_file.name)
        return tmp_file.name

# --- 4. Session State ---
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""

# --- 5. Giao diện ---
st.title("🎙️ VisionVoice Pro")
st.caption("Sử dụng Gemini 1.5 Flash & Giọng đọc Neural siêu thực")

col1, col2 = st.columns(2, gap="large")

# === CỘT TRÁI: INPUT ===
with col1:
    st.subheader("🖼️ Hình ảnh")
    uploaded_file = st.file_uploader("Tải ảnh lên", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh gốc", use_column_width=True)
        
        if st.button("🔍 Quét văn bản (OCR)", type="primary", use_container_width=True):
            with st.spinner("Đang đọc ảnh..."):
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(["Trích xuất nguyên văn nội dung văn bản trong ảnh này.", image])
                    st.session_state['extracted_text'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

# === CỘT PHẢI: OUTPUT ===
with col2:
    st.subheader("📝 Văn bản & Giọng nói")
    
    text_content = st.text_area(
        "Nội dung:",
        value=st.session_state['extracted_text'],
        height=300
    )
    
    # Cập nhật lại nếu sửa tay
    if text_content != st.session_state['extracted_text']:
         st.session_state['extracted_text'] = text_content

    st.divider()
    
    # Chọn giọng đọc (Các giọng xịn của Microsoft)
    voice_options = {
        "Tiếng Việt - Hoài My (Nữ - Nhẹ nhàng)": "vi-VN-HoaiMyNeural",
        "Tiếng Việt - Nam Minh (Nam - Trầm ấm)": "vi-VN-NamMinhNeural",
        "Tiếng Anh - Aria (Nữ)": "en-US-AriaNeural",
        "Tiếng Anh - Christopher (Nam)": "en-US-ChristopherNeural"
    }
    
    selected_voice_label = st.selectbox("Chọn giọng đọc:", list(voice_options.keys()))
    selected_voice_code = voice_options[selected_voice_label]

    if st.button("🔊 Đọc Ngay (Neural Voice)", use_container_width=True):
        if text_content.strip():
            with st.spinner("Đang tạo giọng nói (Mất khoảng 2-3 giây)..."):
                try:
                    # Chạy hàm bất đồng bộ (async)
                    audio_file_path = asyncio.run(text_to_speech_edge(text_content, selected_voice_code))
                    
                    # Phát âm thanh
                    st.audio(audio_file_path, format='audio/mp3')
                    st.success("Đã tạo xong!")
                except Exception as e:
                    st.error(f"Lỗi giọng nói: {e}")
        else:
            st.warning("Chưa có nội dung để đọc!")
