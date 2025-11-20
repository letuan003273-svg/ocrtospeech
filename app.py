import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- Cấu hình trang ---
st.set_page_config(page_title="VisionVoice Clone", page_icon="✨")

# --- Cấu hình API Key ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("Chưa tìm thấy API Key.")
        st.stop()
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

# --- Tiêu đề và Mô tả ---
st.title("✨ VisionVoice")
st.write("Upload an image, or type text to listen with lifelike AI speech.")

# --- Tạo khung giao diện chính ---
# Sử dụng container để đóng gói giao diện
with st.container():
    # 1. Tạo nút chuyển đổi (Toggle) giữa File và Text
    option = st.radio(
        "Source",
        ["File", "Text"],
        horizontal=True, # Giúp nút nằm ngang giống trong ảnh
        label_visibility="visible"
    )

    st.divider() # Đường kẻ ngang

    # 2. Xử lý trường hợp chọn "File"
    if option == "File":
        uploaded_file = st.file_uploader(
            "Click to upload", 
            type=["jpg", "png", "jpeg"], 
            help="Upload ảnh để AI phân tích"
        )
        
        if uploaded_file is not None:
            # Hiển thị ảnh vừa upload
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh đã tải lên", use_column_width=True)
            
            # Nút bấm để phân tích
            if st.button("Phân tích ảnh này"):
                with st.spinner("Đang suy nghĩ..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(["Mô tả chi tiết bức ảnh này bằng tiếng Việt.", image])
                        st.success("Kết quả phân tích:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

    # 3. Xử lý trường hợp chọn "Text"
    else:
        text_input = st.text_area("Nhập văn bản của bạn vào đây...", height=150)
        if st.button("Gửi văn bản"):
            if text_input:
                 with st.spinner("Đang xử lý..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(text_input)
                    st.write(response.text)
