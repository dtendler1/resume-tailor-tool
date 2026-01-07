import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import time
from google.api_core import exceptions

# Setup Page
st.set_page_config(page_title="Resume Tailor Pro", layout="wide")
st.title("🎯 Smart CV-to-JD Tailoring Dashboard")

# 1. Sidebar for Setup
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    tone = st.selectbox("Select Tone", ["Professional/Corporate", "Modern/Startup", "Technical/Academic"])
    st.info("Note: If you hit a limit, the app will automatically wait and retry.")

# 2. Main Interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Documents")
    cv_file = st.file_uploader("Upload Original CV (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("Paste Job Description (JD) here", height=300)

def extract_text(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return " ".join([page.extract_text() for page in reader.pages])
    else:
        doc = Document(file)
        return " ".join([p.text for p in doc.paragraphs])

# 3. Processing Logic with Auto-Retry
if st.button("Tailor My CV"):
    if not api_key:
        st.error("Please enter your API key in the sidebar!")
    elif not cv_file or not jd_text:
        st.warning("Please upload a CV and paste a JD.")
    else:
        status_box = st.empty()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        cv_text = extract_text(cv_file)
        
        prompt = f"ROLE: ATS Optimizer. CV: {cv_text} JD: {jd_text} TONE: {tone}. (Instructions: 75% retention, 40% relevance check, no bold keywords)."

        # --- RETRY LOGIC START ---
        max_retries = 5
        for i in range(max_retries):
            try:
                with st.spinner(f"Processing... (Attempt {i+1})"):
                    response = model.generate_content(prompt)
                
                with col2:
                    st.subheader("Optimized Result")
                    if "RELEVANCE ALERT" in response.text:
                        st.warning(response.text)
                    else:
                        st.success("CV Successfully Tailored!")
                        st.text_area("Copy your new CV content:", value=response.text, height=600)
                break # Exit the loop if successful

            except exceptions.ResourceExhausted:
                wait_time = (2 ** i) + 2 # Exponential backoff: 3s, 4s, 6s...
                status_box.warning(f"Quota reached. Waiting {wait_time}s to retry...")
                time.sleep(wait_time)
                if i == max_retries - 1:
                    st.error("Maximum retries reached. Please wait 1 minute and try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                break
        # --- RETRY LOGIC END ---
