import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import io

# --- 1. Cấu hình trang ---
st.set_page_config(page_title="VisionVoice Pro", page_icon="💎", layout="wide")

# --- 2. GIAO DIỆN CẤU HÌNH KEY (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Quản lý API Key")
    st.markdown("Nếu Key mặc định hết hạn, hãy nhập Key mới vào dưới đây để tiếp tục dùng ngay lập tức.")
    
    # Kiểm tra trạng thái Key Google
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("✅ Google API Key: Đã kết nối")
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Chưa có Google API Key trong Secrets")
    
    st.divider()
    
    # --- QUẢN LÝ ELEVENLABS KEY ---
    st.subheader("ElevenLabs Key")
    
    # 1. Kiểm tra Key trong Secrets
    default_eleven_key = st.secrets.get("ELEVENLABS_API_KEY", None)
    if default_eleven_key:
        st.info(f"Key mặc định (Secrets): •••••{default_eleven_key[-4:]}")
    else:
        st.warning("Chưa có Key mặc định trong Secrets.")
        
    # 2. Ô nhập Key dự phòng (Ưu tiên dùng cái này nếu có nhập)
    custom_eleven_key = st.text_input(
        "Nhập Key khác (Ưu tiên):", 
        type="password",
        placeholder="sk_..."
    )
    
    # Logic chọn Key: Nếu có nhập tay thì dùng nhập tay, không thì dùng mặc định
    FINAL_ELEVEN_KEY = custom_eleven_key if custom_eleven_key else default_eleven_key

# --- 3. Hàm gọi API ElevenLabs ---
def text_to_speech_elevenlabs(text, voice_id, api_key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 401:
            st.error("❌ Lỗi 401: API Key này không hợp lệ hoặc đã hết hạn.")
            return None
        else:
            st.error(f"Lỗi ElevenLabs ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

# --- 4. Session State ---
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""

# --- 5. Giao diện Chính ---
st.title("💎 VisionVoice Pro")
st.caption("Hỗ trợ thay đổi nhiều API Key linh hoạt")

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
                    response = model.generate_content(["Trích xuất nội dung văn bản.", image])
                    st.session_state['extracted_text'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi OCR: {e}")

# === CỘT PHẢI: OUTPUT ===
with col2:
    st.subheader("📝 & 🔊 ElevenLabs")
    
    text_content = st.text_area("Nội dung:", value=st.session_state['extracted_text'], height=250)
    
    if text_content != st.session_state['extracted_text']:
         st.session_state['extracted_text'] = text_content

    st.divider()
    
    voice_options = {
        "Rachel (Nữ - Chuẩn)": "21m00Tcm4TlvDq8ikWAM",
        "Clyde (Nam - Trầm)": "2EiwWnXFnvU5JabPnv8n",
        "Mimi (Nữ - Trẻ con)": "ZrHiDhxje0jIeF18mMVI",
        "Fin (Nam - Mạnh)": "D38z5RcWu1voky8WS1ja"
    }
    selected_voice_name = st.selectbox("Chọn giọng:", list(voice_options.keys()))
    selected_voice_id = voice_options[selected_voice_name]

    if st.button("🔊 Đọc Ngay", type="secondary", use_container_width=True):
        if not FINAL_ELEVEN_KEY:
            st.error("⛔ Chưa có API Key! Vui lòng nhập Key vào thanh bên trái.")
        elif text_content.strip():
            with st.spinner("ElevenLabs đang xử lý..."):
                audio_bytes = text_to_speech_elevenlabs(text_content, selected_voice_id, FINAL_ELEVEN_KEY)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success("Xong!")
        else:
            st.warning("Chưa có nội dung!")
