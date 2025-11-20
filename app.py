import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- 1. Cấu hình trang ---
st.set_page_config(page_title="VisionVoice", page_icon="🎙️", layout="wide")

# --- 2. Cấu hình API Key ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Chưa tìm thấy API Key.")
        st.stop()
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

# --- 3. Session State ---
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""

# --- 4. Giao diện ---
st.title("🎙️ VisionVoice (Stable)")
st.caption("Trích xuất văn bản & Đọc thành tiếng (Google TTS)")

col1, col2 = st.columns(2, gap="large")

# === CỘT TRÁI: INPUT ===
with col1:
    st.subheader("🖼️ Hình ảnh")
    uploaded_file = st.file_uploader("Tải ảnh lên", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh gốc", use_column_width=True)
        
        if st.button("🔍 Quét văn bản (OCR)", type="primary", use_container_width=True):
            with st.spinner("Gemini đang đọc ảnh..."):
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    # Prompt kỹ hơn để đảm bảo lấy đúng nội dung
                    response = model.generate_content(["Hãy trích xuất chính xác toàn bộ nội dung văn bản trong ảnh này. Không thêm lời dẫn.", image])
                    st.session_state['extracted_text'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

# === CỘT PHẢI: OUTPUT ===
with col2:
    st.subheader("📝 Kết quả & Đọc")
    
    text_content = st.text_area(
        "Nội dung trích xuất:",
        value=st.session_state['extracted_text'],
        height=300
    )
    
    # Cập nhật lại nếu sửa tay
    if text_content != st.session_state['extracted_text']:
         st.session_state['extracted_text'] = text_content

    st.divider()
    
    # Chọn ngôn ngữ cho gTTS
    # gTTS dùng mã ngôn ngữ: 'vi', 'en', 'ja', 'ko'...
    lang_map = {
        "Tiếng Việt": "vi",
        "Tiếng Anh": "en",
        "Tiếng Nhật": "ja",
        "Tiếng Hàn": "ko",
        "Tiếng Pháp": "fr"
    }
    
    c1, c2 = st.columns([1, 1])
    with c1:
        selected_lang = st.selectbox("Ngôn ngữ đọc:", list(lang_map.keys()))
        lang_code = lang_map[selected_lang]
    
    with c2:
        st.write("") # Căn dòng
        st.write("") 
        if st.button("🔊 Đọc Ngay", use_container_width=True):
            if text_content.strip():
                try:
                    # Sử dụng gTTS (Google Translate Text-to-Speech)
                    # Ưu điểm: Ổn định 100%, không bao giờ bị chặn IP
                    tts = gTTS(text=text_content, lang=lang_code, slow=False)
                    
                    # Lưu vào bộ nhớ đệm
                    sound_file = io.BytesIO()
                    tts.write_to_fp(sound_file)
                    
                    # Phát âm thanh
                    st.audio(sound_file, format='audio/mp3')
                except Exception as e:
                    st.error(f"Lỗi tạo âm thanh: {e}")
            else:
                st.warning("Chưa có nội dung để đọc!")
