import streamlit as st
import os
import tempfile
from src.video_to_pdf import convert_video_to_pdf

st.set_page_config(page_title="Video to PDF Converter", layout="centered")

# Glassmorphic CSS
st.markdown(
    """
    <style>
    .glass {
        background: rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 2.5rem 2rem 2rem 2rem;
        margin: 2rem auto;
        max-width: 420px;
    }
    .stApp {
        background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
    }
    .glass h2, .glass label, .glass p {
        color: #222;
        font-weight: 400;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown("<h2>Video to PDF Converter</h2>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov", "mkv"])

frame_interval = st.number_input(
    "Frame interval (capture every N frames)", min_value=1, max_value=300, value=30, step=1
)
max_duration = st.number_input(
    "Max video duration (seconds)", min_value=10, max_value=7200, value=3600, step=10
)

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as temp_video:
        temp_video.write(uploaded_file.read())
        temp_video_path = temp_video.name
    
    output_pdf_path = tempfile.mktemp(suffix=".pdf")
    
    if st.button("Convert to PDF"):
        with st.spinner("Processing video and generating PDF..."):
            try:
                convert_video_to_pdf(
                    video_path=temp_video_path,
                    output_pdf=output_pdf_path,
                    frame_interval=frame_interval,
                    max_duration=max_duration
                )
                with open(output_pdf_path, "rb") as f:
                    st.download_button(
                        label="Download PDF",
                        data=f,
                        file_name="output.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                os.remove(temp_video_path)
                if os.path.exists(output_pdf_path):
                    os.remove(output_pdf_path)

st.markdown('</div>', unsafe_allow_html=True) 