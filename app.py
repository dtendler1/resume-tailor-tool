import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import io

# Setup Page
st.set_page_config(page_title="Resume Tailor Pro", layout="wide")
st.title("🎯 Smart CV-to-JD Tailoring Dashboard")

# 1. Sidebar for Setup
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    tone = st.selectbox("Select Tone", ["Professional/Corporate", "Modern/Startup", "Technical/Academic"])
    
# 2. Main Interface
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Documents")
    cv_file = st.file_uploader("Upload Original CV (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("Paste Job Description (JD) here", height=300)

# Helper function to extract text
def extract_text(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return " ".join([page.extract_text() for page in reader.pages])
    else:
        doc = Document(file)
        return " ".join([p.text for p in doc.paragraphs])

# 3. Processing Logic
if st.button("Tailor My CV"):
    if not api_key:
        st.error("Please enter your API key in the sidebar!")
    elif not cv_file or not jd_text:
        st.warning("Please upload a CV and paste a JD.")
    else:
        with st.spinner("Analyzing relevance and tailoring..."):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            cv_text = extract_text(cv_file)
            
            # The System Prompt we built
            prompt = f"""
            ROLE: Expert ATS Optimizer.
            
            TASK: Compare the CV and JD provided below. 
            
            CV: {cv_text}
            JD: {jd_text}
            
            TONE: {tone}

            INSTRUCTIONS:
            1. RELEVANCE AUDIT: If the CV is a <40% match for the JD, output ONLY: "⚠️ RELEVANCE ALERT: This JD is a significant mismatch."
            2. If relevant, rewrite the CV.
            3. Keep 75% of original phrasing.
            4. Never invent experience.
            5. Maintain original flow. No bold keywords.
            """
            
            response = model.generate_content(prompt)
            
            with col2:
                st.subheader("Optimized Result")
                if "RELEVANCE ALERT" in response.text:
                    st.warning(response.text)
                else:
                    st.success("CV Successfully Tailored!")
                    st.text_area("Copy your new CV content:", value=response.text, height=600)
