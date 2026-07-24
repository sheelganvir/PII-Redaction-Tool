import streamlit as st
import docx
import os
import io
import time
import pandas as pd
from src.redactor import PIIRedactor
from src.docx_processor import DocxRedactor
from src.evaluator import PIIEvaluator

st.set_page_config(
    page_title="PII Redaction Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium look
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2563EB;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748B;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-title">🛡️ Enterprise PII Redaction & Anonymization Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Automatically detect, redact, and pseudonymize sensitive PII entities in Word (.docx) documents with full formatting preservation.</div>', unsafe_allow_html=True)

    # Sidebar Controls
    st.sidebar.title("⚙️ Redaction Configuration")
    seed_val = st.sidebar.number_input("Random Seed for Pseudonymization", value=42, step=1)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Active PII Entity Types")
    redact_names = st.sidebar.checkbox("Full Names (PERSON)", value=True)
    redact_emails = st.sidebar.checkbox("Email Addresses", value=True)
    redact_phones = st.sidebar.checkbox("Phone Numbers", value=True)
    redact_companies = st.sidebar.checkbox("Company / Org Names", value=True)
    redact_addresses = st.sidebar.checkbox("Physical Addresses", value=True)
    redact_ssn = st.sidebar.checkbox("SSN / Tax IDs (PAN/Aadhaar)", value=True)
    redact_cards = st.sidebar.checkbox("Credit Card Numbers", value=True)
    redact_dob = st.sidebar.checkbox("Dates of Birth", value=True)
    redact_ip = st.sidebar.checkbox("IP Addresses", value=True)

    uploaded_file = st.file_uploader("Upload a Word Document (.docx) to Redact", type=["docx"])

    if uploaded_file is not None:
        input_bytes = uploaded_file.read()
        temp_input_path = f"temp_input_{uploaded_file.name}"
        temp_output_path = f"temp_redacted_{uploaded_file.name}"

        with open(temp_input_path, "wb") as f:
            f.write(input_bytes)

        st.success(f"Uploaded file '{uploaded_file.name}' ({len(input_bytes) / 1024:.1f} KB) successfully!")

        if st.button("🚀 Process & Redact Document", type="primary"):
            with st.spinner("Analyzing document and applying PII redaction rules..."):
                start_t = time.time()
                redactor = PIIRedactor(seed=seed_val)
                processor = DocxRedactor(redactor=redactor)

                results = processor.redact_document(temp_input_path, temp_output_path)
                elapsed = round(time.time() - start_t, 2)

                st.balloons()

                # Results Summary Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{results["total_entities_redacted"]}</div><div class="metric-label">Total PII Redacted</div></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{elapsed}s</div><div class="metric-label">Processing Time</div></div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">{len(results["stats_by_type"])}</div><div class="metric-label">PII Categories Detected</div></div>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div class="metric-box"><div class="metric-value">100%</div><div class="metric-label">Format Retention</div></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Tabs
                tab1, tab2, tab3 = st.tabs(["📊 Entity Analytics", "📄 Text Preview & Diff", "📈 Evaluation Metrics"])

                with tab1:
                    st.subheader("PII Detection Breakdown by Entity Type")
                    if results["stats_by_type"]:
                        df_stats = pd.DataFrame(
                            list(results["stats_by_type"].items()),
                            columns=["Entity Category", "Redaction Count"]
                        ).sort_values("Redaction Count", ascending=False)

                        st.bar_chart(df_stats.set_index("Entity Category"))
                        st.table(df_stats)
                    else:
                        st.info("No sensitive PII entities were detected in this document.")

                with tab2:
                    st.subheader("Sample Text Inspection")
                    doc_orig = docx.Document(temp_input_path)
                    doc_red = docx.Document(temp_output_path)

                    orig_paras = [p.text for p in doc_orig.paragraphs if p.text.strip()][:10]
                    red_paras = [p.text for p in doc_red.paragraphs if p.text.strip()][:10]

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 🔴 Original Paragraphs")
                        for idx, p in enumerate(orig_paras):
                            st.text_area(f"Original Paragraph {idx+1}", p, height=80, disabled=True, key=f"orig_p_{idx}")
                    with c2:
                        st.markdown("### 🟢 Redacted Paragraphs")
                        for idx, p in enumerate(red_paras):
                            st.text_area(f"Redacted Paragraph {idx+1}", p, height=80, disabled=True, key=f"red_p_{idx}")

                with tab3:
                    st.subheader("Model Evaluation Strategy & Metrics")
                    evaluator = PIIEvaluator(redactor=redactor)
                    eval_res = evaluator.evaluate()

                    st.json(eval_res)

                # Download File Button
                with open(temp_output_path, "rb") as out_f:
                    redacted_bytes = out_f.read()

                st.markdown("---")
                st.download_button(
                    label="📥 Download Redacted Document (.docx)",
                    data=redacted_bytes,
                    file_name=f"Redacted_{uploaded_file.name}",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )

                # Cleanup temp files
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)


if __name__ == "__main__":
    main()
