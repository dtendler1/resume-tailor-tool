import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import time
from google.api_core import exceptions

# 1. Setup Page
st.set_page_config(page_title="AI Resume Tailor Pro", layout="wide")
st.title("🎯 Smart CV-to-JD Tailoring Dashboard")

# 2. Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password", help="Get your key from Google AI Studio")
    tone = st.selectbox("Select Resume Tone", ["Professional/Corporate", "Modern/Startup", "Technical/Academic"])
    st.markdown("---")
    st.info("💡 **Free Tier Tip:** If you see a 'Quota' message, the app will automatically wait and retry for you.")

# 3. Main Interface Columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Upload Documents")
    cv_file = st.file_uploader("Upload Original CV (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("Paste Job Description (JD) here", height=300, placeholder="Paste the requirements...")

# 4. Document Parsing Helper
def extract_text(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        doc = Document(file)
        return " ".join([p.text for p in doc.paragraphs])

# 5. Processing Logic with Auto-Retry
if st.button("🚀 Start Tailoring"):
    if not api_key:
        st.error("Please enter your API key in the sidebar!")
    elif not cv_file or not jd_text:
        st.warning("Please upload both your CV and the JD.")
    else:
        status_box = st.empty()
        genai.configure(api_key=api_key)
        
        # Using 2.0-flash-lite for better free-tier reliability
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        cv_text = extract_text(cv_file)
        
        prompt = f"""
        ACT AS: Expert Resume Writer.
        CV: {cv_text}
        JD: {jd_text}
        TONE: {tone}
        RULES:
        1. RELEVANCE AUDIT: If CV is <40% relevant to JD, ONLY write: "⚠️ RELEVANCE ALERT: This JD is a significant mismatch."
        2. Keep 75% of original CV phrasing.
        3. Never invent facts. No bold keywords.
        """

        # Retry Logic for Quota issues
        max_retries = 4
        for i in range(max_retries):
            try:
                with st.spinner(f"Analyzing... (Attempt {i+1}/{max_retries})"):
                    response = model.generate_content(prompt)
                
                with col2:
                    st.subheader("✨ Tailored CV Result")
                    if "RELEVANCE ALERT" in response.text:
                        st.warning(response.text)
                    else:
                        st.success("CV Successfully Optimized!")
                        st.text_area("Copy your new CV:", value=response.text, height=600)
                break 

            except exceptions.ResourceExhausted:
                wait_time = (i + 1) * 20 
                status_box.warning(f"⏳ Quota reached. Resetting in {wait_time}s...")
                time.sleep(wait_time)
                if i == max_retries - 1:
                    st.error("❌ Max retries reached. Please wait 1 minute and try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                break
