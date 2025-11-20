import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- 1. Cấu hình trang (Layout Wide để chia 2 cột) ---
st.set_page_config(page_title="VisionVoice", page_icon="✨", layout="wide")

# --- 2. Cấu hình API Key ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Chưa tìm thấy API Key trong Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

# --- 3. CSS Tùy chỉnh để giống giao diện Card (Tùy chọn) ---
st.markdown("""
<style>
    .stTextArea textarea {
        background-color: #f0f2f6;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. Khởi tạo Session State (Để lưu văn bản sau khi AI quét xong) ---
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""

# --- 5. Header ---
st.markdown("<h1 style='text-align: center;'>✨ VisionVoice</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Upload an image to extract text and listen with AI speech.</p>", unsafe_allow_html=True)
st.write("") # Khoảng trắng

# --- 6. Giao diện chính (Chia 2 cột) ---
col1, col2 = st.columns(2, gap="large")

# === CỘT TRÁI: INPUT (SOURCE) ===
with col1:
    st.subheader("🖼️ Source")
    
    # Tab chọn File hoặc Text (Giả lập bằng Radio)
    source_type = st.radio("Chọn nguồn:", ["File Upload", "Nhập tay"], horizontal=True, label_visibility="collapsed")
    
    if source_type == "File Upload":
        # Khung upload ảnh
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            # Hiển thị ảnh
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh gốc", use_column_width=True)
            
            # Nút Quét chữ (OCR)
            if st.button("🔍 Trích xuất văn bản (OCR)", type="primary", use_container_width=True):
                with st.spinner("Gemini đang đọc ảnh..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        # Prompt yêu cầu chỉ trích xuất chữ
                        response = model.generate_content(["Hãy trích xuất toàn bộ văn bản có trong bức ảnh này. Chỉ trả về nội dung văn bản, không thêm lời bình luận.", image])
                        st.session_state['extracted_text'] = response.text
                        st.rerun() # Tải lại trang để cập nhật cột bên phải
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
    else:
        st.info("Chuyển sang chế độ nhập tay bên cột phải ->")

# === CỘT PHẢI: OUTPUT (CONTENT & TTS) ===
with col2:
    st.subheader("📝 Content")
    
    # Ô hiển thị văn bản (Cho phép sửa)
    text_content = st.text_area(
        "Nội dung văn bản:",
        value=st.session_state['extracted_text'],
        height=300,
        placeholder="Văn bản được trích xuất sẽ hiện ở đây...",
        label_visibility="collapsed"
    )
    
    # Cập nhật lại session state nếu người dùng sửa bằng tay
    if text_content != st.session_state['extracted_text']:
         st.session_state['extracted_text'] = text_content

    st.divider()
    
    # Khu vực điều khiển giọng nói
    c1, c2 = st.columns([1, 2])
    with c1:
        # Chọn ngôn ngữ đọc
        lang_option = st.selectbox("Giọng đọc", ["Tiếng Việt (vi)", "English (en)", "Korean (ko)", "Japanese (ja)"])
        lang_code = lang_option.split("(")[1].replace(")", "") # Lấy mã 'vi', 'en'...
    
    with c2:
        st.write("") # Căn chỉnh lề
        st.write("") 
        if st.button("🔊 Read Aloud (Đọc ngay)", use_container_width=True):
            if text_content.strip():
                try:
                    # Sử dụng gTTS để tạo file âm thanh
                    tts = gTTS(text=text_content, lang=lang_code)
                    
                    # Lưu vào bộ nhớ đệm thay vì lưu file cứng
                    sound_file = io.BytesIO()
                    tts.write_to_fp(sound_file)
                    
                    # Phát âm thanh
                    st.audio(sound_file, format='audio/mp3')
                except Exception as e:
                    st.error(f"Lỗi tạo giọng nói: {e}")
            else:
                st.warning("Chưa có nội dung để đọc!")
