import streamlit as st
import google.generativeai as genai
from PIL import Image
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# --- 1. Cấu hình trang ---
st.set_page_config(page_title="VisionVoice Pro (ElevenLabs)", page_icon="💎", layout="wide")

# --- 2. Kiểm tra và lấy API Key từ Secrets ---
try:
    # Key Google
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Thiếu GOOGLE_API_KEY.")
        st.stop()
        
    # Key ElevenLabs
    if "ELEVENLABS_API_KEY" in st.secrets:
        elevenlabs_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])
    else:
        st.error("⚠️ Thiếu ELEVENLABS_API_KEY.")
        st.stop()

except Exception as e:
    st.error(f"Lỗi cấu hình Secrets: {e}")

# --- 3. Session State ---
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""

# --- 4. Giao diện ---
st.title("💎 VisionVoice Pro")
st.caption("Powered by Gemini 1.5 & ElevenLabs (Giọng đọc AI cao cấp)")

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
                    response = model.generate_content(["Trích xuất toàn bộ nội dung văn bản trong ảnh này. Chỉ trả về văn bản.", image])
                    st.session_state['extracted_text'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi OCR: {e}")

# === CỘT PHẢI: OUTPUT ===
with col2:
    st.subheader("📝 & 🔊 ElevenLabs TTS")
    
    text_content = st.text_area(
        "Nội dung:",
        value=st.session_state['extracted_text'],
        height=250
    )
    
    if text_content != st.session_state['extracted_text']:
         st.session_state['extracted_text'] = text_content

    st.divider()
    
    # Cấu hình giọng đọc ElevenLabs
    # Bạn có thể thêm Voice ID khác lấy từ trang ElevenLabs
    voice_options = {
        "Rachel (Nữ - Tiếng Anh chuẩn)": "21m00Tcm4TlvDq8ikWAM",
        "Clyde (Nam - Trầm ấm)": "2EiwWnXFnvU5JabPnv8n",
        "Mimi (Nữ - Nhí nhảnh)": "ZrHiDhxje0jIeF18mMVI",
        "Fin (Nam - Mạnh mẽ)": "D38z5RcWu1voky8WS1ja"
    }
    
    st.info("💡 Lưu ý: ElevenLabs Free giới hạn 10.000 ký tự/tháng.")
    
    selected_voice_name = st.selectbox("Chọn giọng (Voice ID):", list(voice_options.keys()))
    selected_voice_id = voice_options[selected_voice_name]

    if st.button("🔊 Đọc bằng ElevenLabs", type="secondary", use_container_width=True):
        if text_content.strip():
            with st.spinner("Đang kết nối máy chủ ElevenLabs (Xin chờ)..."):
                try:
                    # Gọi API ElevenLabs
                    # model_id="eleven_multilingual_v2" là BẮT BUỘC để đọc tiếng Việt
                    audio_stream = elevenlabs_client.generate(
                        text=text_content,
                        voice=selected_voice_id,
                        model="eleven_multilingual_v2"
                    )
                    
                    # Phát âm thanh trực tiếp (Streamlit tự xử lý byte stream)
                    st.audio(audio_stream, format="audio/mp3")
                    st.success("Đã tạo xong!")
                    
                except Exception as e:
                    st.error(f"Lỗi ElevenLabs: {e}")
                    st.warning("Gợi ý: Kiểm tra xem tài khoản ElevenLabs của bạn còn 'quota' (số lượng ký tự) miễn phí không.")
        else:
            st.warning("Chưa có nội dung để đọc!")
