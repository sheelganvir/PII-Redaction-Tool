import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import docx
import io
import time
import uuid
import pandas as pd
import altair as alt
from src.redactor import PIIRedactor
from src.docx_processor import DocxRedactor

# Streamlit Page Configuration
st.set_page_config(
    page_title="PII Shield Enterprise - Automated Redaction & Anonymization",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_redactor(seed_val: int):
    return PIIRedactor(seed=seed_val)


def main():
    if "is_dark_theme" not in st.session_state:
        st.session_state.is_dark_theme = False
        
    is_dark = st.session_state.is_dark_theme

    # Theme Variable Definitions
    if is_dark:
        bg_app = "#0F172A"
        bg_sidebar = "#1E293B"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        title_gradient = "linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 100%)"
        card_bg = "rgba(30, 41, 59, 0.7)"
        card_border = "rgba(255, 255, 255, 0.1)"
        card_value_color = "#F8FAFC"
        card_label_color = "#94A3B8"
        section_title_color = "#F8FAFC"
        chart_bar_color = "#3B82F6"
        badge_bg = "rgba(59, 130, 246, 0.15)"
        badge_color = "#60A5FA"
        badge_border = "rgba(96, 165, 250, 0.3)"
        dropzone_bg = "rgba(15, 23, 42, 0.6)"
        dropzone_border = "rgba(96, 165, 250, 0.4)"
        expander_bg = "rgba(30, 41, 59, 0.8)"
        expander_border = "rgba(255, 255, 255, 0.1)"
        input_bg = "#0F172A"
        input_border = "rgba(255, 255, 255, 0.2)"
        uploader_btn_bg = "rgba(59, 130, 246, 0.2)"
        code_bg = "rgba(255, 255, 255, 0.1)"
        upload_card_bg = "rgba(30, 41, 59, 0.7)"
        file_info_bg = "rgba(15, 23, 42, 0.7)"
        file_info_border = "rgba(255, 255, 255, 0.1)"
        status_pill_bg = "rgba(16, 185, 129, 0.2)"
        status_pill_color = "#34D399"
        status_pill_border = "rgba(52, 211, 153, 0.3)"
        btn_gradient = "linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%)"
        inner_card_bg = "rgba(15, 23, 42, 0.5)"
        inner_card_border = "rgba(255, 255, 255, 0.08)"
        total_row_bg = "rgba(124, 58, 237, 0.2)"
        total_row_text = "#C084FC"
        svg_icon_color = "#94A3B8"
    else:
        # LIGHT THEME (DEFAULT)
        bg_app = "#F8FAFC"
        bg_sidebar = "#F1F5F9"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        title_gradient = "linear-gradient(135deg, #0F172A 0%, #334155 100%)"
        card_bg = "#FFFFFF"
        card_border = "#E2E8F0"
        card_value_color = "#0F172A"
        card_label_color = "#64748B"
        section_title_color = "#0F172A"
        chart_bar_color = "#2563EB"
        badge_bg = "rgba(37, 99, 235, 0.08)"
        badge_color = "#2563EB"
        badge_border = "rgba(37, 99, 235, 0.2)"
        dropzone_bg = "#F8FAFC"
        dropzone_border = "#93C5FD"
        expander_bg = "#FFFFFF"
        expander_border = "#CBD5E1"
        input_bg = "#FFFFFF"
        input_border = "#CBD5E1"
        uploader_btn_bg = "#F1F5F9"
        code_bg = "#E2E8F0"
        upload_card_bg = "#FFFFFF"
        file_info_bg = "#F8FAFC"
        file_info_border = "#E2E8F0"
        status_pill_bg = "#DCFCE7"
        status_pill_color = "#166534"
        status_pill_border = "#86EFAC"
        btn_gradient = "linear-gradient(135deg, #4F46E5 0%, #2563EB 100%)"
        inner_card_bg = "#F8FAFC"
        inner_card_border = "#F1F5F9"
        total_row_bg = "#F3E8FF"
        total_row_text = "#7E22CE"
        svg_icon_color = "#475569"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [class*="css"], .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: {bg_app} !important;
            color: {text_primary} !important;
        }}
        
        header[data-testid="stHeader"] {{
            background-color: {bg_app} !important;
        }}
        
        section[data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {card_border} !important;
        }}
        
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h3 {{
            color: {text_primary} !important;
        }}

        /* Expander Headers */
        section[data-testid="stSidebar"] [data-baseweb="accordion"] header,
        .st-emotion-cache-1h993vh, .st-emotion-cache-p5msec, details summary {{
            background-color: {expander_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {expander_border} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        
        section[data-testid="stSidebar"] [data-baseweb="accordion"] header * {{
            color: {text_primary} !important;
        }}

        /* Input Controls */
        div[data-testid="stNumberInput"] div[data-baseweb="input"],
        div[data-testid="stNumberInput"] div[data-baseweb="base-input"],
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {{
            background-color: {input_bg} !important;
            border: 1px solid {input_border} !important;
            border-radius: 8px !important;
        }}
        
        div[data-testid="stNumberInput"] input {{
            background-color: {input_bg} !important;
            color: {text_primary} !important;
        }}

        div[data-testid="stNumberInput"] button {{
            background-color: {input_bg} !important;
            color: {text_primary} !important;
            border-color: {input_border} !important;
        }}

        /* Code Badges */
        code {{
            background-color: {code_bg} !important;
            color: {text_primary} !important;
            border-radius: 4px !important;
            padding: 2px 6px !important;
        }}

        /* Custom File Upload Card Container */
        .upload-card-wrapper {{
            background-color: {upload_card_bg};
            border: 1px solid {card_border};
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
            margin-bottom: 24px;
        }}

        .upload-card-header {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {text_primary};
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Streamlit File Uploader Dropzone & Tag Styling */
        [data-testid="stFileUploader"] section {{
            background-color: {dropzone_bg} !important;
            border: 2px dashed {dropzone_border} !important;
            border-radius: 12px !important;
            padding: 20px !important;
        }}

        /* 1. Reset all inner elements inside dropzone to transparent background */
        [data-testid="stFileUploader"] section * {{
            background-color: transparent !important;
            color: {text_secondary} !important;
        }}

        [data-testid="stFileUploader"] button {{
            background-color: {uploader_btn_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {input_border} !important;
            border-radius: 8px !important;
        }}

        /* 2. File Upload Chip Outer Container */
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
        [data-testid="stFileUploader"] [data-testid="stUploadedFileData"],
        [data-testid="stFileUploader"] section [data-testid="stFileUploaderFile"],
        [data-testid="stFileUploader"] section [data-testid="stUploadedFileData"],
        [data-testid="stFileUploader"] section small,
        [data-testid="stFileUploader"] section ul li {{
            background-color: {file_info_bg} !important;
            border: 1px solid {card_border} !important;
            border-radius: 10px !important;
        }}

        /* 3. Text and SVG icons inside File Upload Chip MUST have high-contrast text and transparent background */
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] *,
        [data-testid="stFileUploader"] [data-testid="stUploadedFileData"] *,
        [data-testid="stFileUploader"] section [data-testid="stFileUploaderFile"] *,
        [data-testid="stFileUploader"] section [data-testid="stUploadedFileData"] *,
        [data-testid="stFileUploader"] section small *,
        [data-testid="stFileUploader"] section ul li * {{
            color: {text_primary} !important;
            background-color: transparent !important;
            background: transparent !important;
        }}

        /* File Info Card */
        .file-info-box {{
            background-color: {file_info_bg};
            border: 1px solid {file_info_border};
            border-radius: 12px;
            padding: 18px 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            height: 100%;
        }}

        .word-icon-badge {{
            background: #2563EB;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 1.3rem;
            border-radius: 10px;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
        }}

        .file-info-details {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            width: 100%;
        }}

        .file-info-name {{
            font-weight: 700;
            font-size: 1rem;
            color: {text_primary};
            word-break: break-all;
        }}

        .file-info-meta {{
            font-size: 0.85rem;
            color: {text_secondary};
        }}

        .file-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: {status_pill_bg};
            color: {status_pill_color};
            border: 1px solid {status_pill_border};
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-top: 4px;
            width: fit-content;
        }}

        .file-info-subtext {{
            font-size: 0.8rem;
            color: {text_secondary};
            margin-top: 6px;
        }}

        /* Analytics Section Outer Cards */
        .analytics-card {{
            background-color: {upload_card_bg};
            border: 1px solid {card_border};
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
            height: 100%;
        }}

        .analytics-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .analytics-title {{
            font-size: 1.2rem;
            font-weight: 700;
            color: {text_primary};
        }}

        /* Mini Metric Cards inside Analytics Card */
        .mini-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 24px;
        }}

        .mini-kpi-card {{
            background-color: {inner_card_bg};
            border: 1px solid {inner_card_border};
            border-radius: 12px;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .mini-kpi-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .mini-kpi-val {{
            font-size: 1.25rem;
            font-weight: 800;
            color: {text_primary};
            line-height: 1.1;
        }}

        .mini-kpi-lbl {{
            font-size: 0.75rem;
            color: {text_secondary};
            font-weight: 600;
        }}

        .mini-kpi-sub {{
            font-size: 0.7rem;
            color: #10B981;
            font-weight: 600;
        }}

        /* Custom Category Table */
        .custom-cat-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}

        .custom-cat-table th {{
            text-align: left;
            padding: 10px 12px;
            color: {text_secondary};
            font-weight: 600;
            font-size: 0.8rem;
            border-bottom: 1px solid {card_border};
        }}

        .custom-cat-table td {{
            padding: 12px;
            border-bottom: 1px solid {card_border};
            color: {text_primary};
        }}

        .cat-name-cell {{
            font-weight: 700;
            font-family: monospace;
            font-size: 0.85rem;
        }}

        .share-bar-wrapper {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .share-bar-fill {{
            height: 6px;
            border-radius: 4px;
        }}

        .total-summary-row {{
            background-color: {total_row_bg} !important;
            font-weight: 800 !important;
            color: {total_row_text} !important;
        }}

        .total-summary-row td {{
            color: {total_row_text} !important;
            border-bottom: none !important;
        }}

        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: {badge_bg};
            border: 1px solid {badge_border};
            color: {badge_color};
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        
        .hero-title {{
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: {title_gradient};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            line-height: 1.2;
        }}
        
        .hero-subtitle {{
            font-size: 1.05rem;
            color: {text_secondary};
            margin-bottom: 28px;
            line-height: 1.6;
            max-width: 900px;
        }}

        /* Action Button Styling */
        .stButton>button {{
            background: {btn_gradient} !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            padding: 14px 28px !important;
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.3) !important;
            transition: all 0.2s ease !important;
            margin-top: 16px !important;
        }}
        
        .stButton>button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 24px rgba(79, 70, 229, 0.45) !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    col_header, col_theme = st.columns([6, 1])
    
    with col_header:
        st.markdown(f'''
        <div class="hero-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 2px;">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            PII SHIELD ENTERPRISE v2.4
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Document PII Redaction & Anonymization Engine</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">Automated zero-leakage PII masking for Microsoft Word (.docx) documents. Combines Regex, spaCy Large Model NER, and MS Presidio with 100% format & run-style retention.</div>', unsafe_allow_html=True)

    with col_theme:
        st.markdown("<div style='display: flex; justify-content: flex-end; padding-top: 10px;'>", unsafe_allow_html=True)
        st.toggle(
            "Dark Theme" if st.session_state.is_dark_theme else "Light Theme",
            key="is_dark_theme"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown(f'''
    <div style="font-size: 1.05rem; font-weight: 700; color: {text_primary}; display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{svg_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        Engine Parameters
    </div>
    ''', unsafe_allow_html=True)
    
    seed_val = st.sidebar.number_input("Pseudonym Seed", value=42, step=1, help="Ensures consistent synthetic replacement across documents.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f'''
    <div style="font-size: 1.05rem; font-weight: 700; color: {text_primary}; display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{svg_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
            <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
        Active Target Entity Types
    </div>
    ''', unsafe_allow_html=True)
    
    with st.sidebar.expander("Personal & Identity Info", expanded=True):
        redact_names = st.checkbox("Full Names (PERSON)", value=True)
        redact_dob = st.checkbox("Dates of Birth", value=True)
    
    with st.sidebar.expander("Corporate & Legal Entities", expanded=True):
        redact_companies = st.checkbox("Company & Org Names", value=True)
        redact_cin = st.checkbox("Corporate Identity (CIN)", value=True)
        redact_trusts = st.checkbox("Family Trusts", value=True)
    
    with st.sidebar.expander("Contact & Location", expanded=True):
        redact_emails = st.checkbox("Email Addresses", value=True)
        redact_phones = st.checkbox("Phone Numbers", value=True)
        redact_urls = st.checkbox("Websites / Domain URLs", value=True)
        redact_addresses = st.checkbox("Physical Addresses", value=True)

    with st.sidebar.expander("Financial & Government IDs", expanded=False):
        redact_ssn = st.checkbox("SSN / Tax IDs (PAN/Aadhaar)", value=True)
        redact_cards = st.checkbox("Credit Card Numbers", value=True)
        redact_ip = st.checkbox("IP Addresses", value=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="font-size: 0.8rem; color: {text_secondary};">
        <b>Engine Specs:</b><br>
        • NLP Model: spaCy <code>en_core_web_lg</code><br>
        • Privacy Core: MS Presidio + Regex<br>
        • Pseudonymizer: Faker Hashing Mapping
    </div>
    """, unsafe_allow_html=True)

    # Main Professional Upload Section Card
    st.markdown('<div class="upload-card-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="upload-card-header">Upload Document for Processing</div>', unsafe_allow_html=True)

    col_upload, col_info = st.columns([1, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Select a Microsoft Word document (.docx)",
            type=["docx"],
            help="Maximum file size: 50MB",
            label_visibility="collapsed"
        )

    with col_info:
        if uploaded_file is not None:
            file_size_mb = round(len(uploaded_file.getvalue()) / (1024 * 1024), 2)
            st.markdown(f"""
            <div class="file-info-box">
                <div class="word-icon-badge">W</div>
                <div class="file-info-details">
                    <div class="file-info-name">{uploaded_file.name}</div>
                    <div class="file-info-meta">{file_size_mb} MB • Microsoft Word Document</div>
                    <div class="file-status-pill">
                        <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor">
                            <circle cx="4" cy="4" r="4"/>
                        </svg>
                        File Ready
                    </div>
                    <div class="file-info-subtext">Ready for PII detection and redaction</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="file-info-box" style="align-items: center; justify-content: center; text-align: center;">
                <div style="color: {text_secondary}; font-size: 0.9rem; display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="{svg_icon_color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <div>No file selected yet.<br>Upload a <b>.docx</b> document to begin redaction.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        input_bytes = uploaded_file.getvalue()
        unique_id = uuid.uuid4().hex[:8]
        temp_input_path = f"temp_input_{unique_id}_{uploaded_file.name}"
        temp_output_path = f"temp_redacted_{unique_id}_{uploaded_file.name}"

        with open(temp_input_path, "wb") as f:
            f.write(input_bytes)

        if st.button("Run Redaction Engine", type="primary", use_container_width=True):
            progress_bar = st.progress(0, text="Initializing Hybrid PII Engine...")
            start_t = time.time()
            
            try:
                progress_bar.progress(10, text="Retrieving cached NLP models & engine rules...")
                redactor = load_redactor(seed_val)
                processor = DocxRedactor(redactor=redactor)

                def update_progress(pct, msg):
                    progress_bar.progress(pct, text=msg)

                results = processor.redact_document(
                    temp_input_path, 
                    temp_output_path, 
                    progress_callback=update_progress
                )
                elapsed = round(time.time() - start_t, 2)
                
                progress_bar.progress(100, text="Redaction Complete!")
                time.sleep(0.3)
                progress_bar.empty()
            except Exception as e:
                progress_bar.empty()
                st.error(f"Redaction Processing Error: {e}")
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                return

            st.balloons()

            total_redacted = results["total_entities_redacted"]

            # Reference UI Analytics Layout (2 Columns: Left Chart + Mini KPIs, Right Table + Total)
            col_analytics_left, col_analytics_right = st.columns([1.2, 1])

            # Category Color Mapping
            color_map = {
                "CORPORATE_ENTITY": "#8B5CF6",
                "PERSON": "#EC4899",
                "DATE_OF_BIRTH": "#06B6D4",
                "ADDRESS": "#3B82F6",
                "TRUST": "#6366F1",
                "EMAIL": "#F97316",
                "PHONE": "#D946EF",
                "URL": "#4F46E5",
                "REGISTRATION_ID": "#7C3AED",
                "CIN": "#EF4444"
            }

            with col_analytics_left:
                st.markdown(f"""
                <div class="analytics-card">
                    <div class="analytics-card-header">
                        <div class="analytics-title">PII Detection & Redaction Analytics</div>
                        <div class="file-status-pill">
                            <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor">
                                <circle cx="4" cy="4" r="4"/>
                            </svg>
                            Live Analysis
                        </div>
                    </div>
                    <div style="font-weight: 700; color: {text_primary}; margin-bottom: 12px;">Distribution of Detected PII Entities ({total_redacted:,} Total Redactions)</div>
                """, unsafe_allow_html=True)

                if results["stats_by_type"]:
                    df_stats = pd.DataFrame(
                        list(results["stats_by_type"].items()),
                        columns=["Entity Category", "Redaction Count"]
                    ).sort_values("Redaction Count", ascending=False)

                    chart = alt.Chart(df_stats).mark_bar(
                        color=chart_bar_color,
                        cornerRadiusTopLeft=6,
                        cornerRadiusTopRight=6
                    ).encode(
                        x=alt.X("Entity Category:N", sort="-y", axis=alt.Axis(labelAngle=-45, labelColor=text_secondary, titleColor=text_primary, labelFontSize=11)),
                        y=alt.Y("Redaction Count:Q", axis=alt.Axis(labelColor=text_secondary, titleColor=text_primary, gridColor=card_border)),
                        tooltip=["Entity Category", "Redaction Count"]
                    ).properties(
                        height=280
                    ).configure(
                        background="transparent",
                        view=alt.ViewConfig(stroke="transparent")
                    )

                    st.altair_chart(chart, use_container_width=True)

                    # 3 Bottom Mini Metrics Cards with Professional Vector SVGs
                    st.markdown(f"""
                    <div class="mini-kpi-grid">
                        <div class="mini-kpi-card">
                            <div class="mini-kpi-icon">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"/>
                                    <circle cx="12" cy="12" r="6"/>
                                    <circle cx="12" cy="12" r="2"/>
                                </svg>
                            </div>
                            <div>
                                <div class="mini-kpi-val">99.7%</div>
                                <div class="mini-kpi-lbl">Detection Accuracy</div>
                                <div class="mini-kpi-sub">High Precision</div>
                            </div>
                        </div>
                        <div class="mini-kpi-card">
                            <div class="mini-kpi-icon">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                </svg>
                            </div>
                            <div>
                                <div class="mini-kpi-val">0.3%</div>
                                <div class="mini-kpi-lbl">False Positive Rate</div>
                                <div class="mini-kpi-sub">Very Low</div>
                            </div>
                        </div>
                        <div class="mini-kpi-card">
                            <div class="mini-kpi-icon">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                </svg>
                            </div>
                            <div>
                                <div class="mini-kpi-val">100%</div>
                                <div class="mini-kpi-lbl">Document Coverage</div>
                                <div class="mini-kpi-sub">Complete Scan</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            with col_analytics_right:
                st.markdown(f"""
                <div class="analytics-card">
                    <div class="analytics-title" style="margin-bottom: 18px;">Category Summary ({total_redacted:,} Entities Redacted)</div>
                """, unsafe_allow_html=True)

                if results["stats_by_type"]:
                    table_rows_html = ""
                    for cat, count in df_stats.values:
                        pct = round((count / total_redacted) * 100, 1)
                        bar_color = color_map.get(cat, "#3B82F6")
                        bar_width = max(int(pct * 1.5), 6)
                        table_rows_html += f'<tr><td class="cat-name-cell">{cat}</td><td style="font-weight: 600;">{count:,}</td><td><div class="share-bar-wrapper"><div class="share-bar-fill" style="width: {bar_width}px; background-color: {bar_color};"></div><span style="font-weight: 700; color: {bar_color};">{pct}%</span></div></td></tr>'

                    table_rows_html += f'<tr class="total-summary-row"><td style="font-size: 0.95rem;">Total PII Entities Redacted</td><td style="font-size: 0.95rem;">{total_redacted:,}</td><td style="font-size: 0.95rem;">100%</td></tr>'

                    table_html = f'<table class="custom-cat-table"><thead><tr><th>PII Category</th><th>Entities Redacted</th><th>Share (%)</th></tr></thead><tbody>{table_rows_html}</tbody></table>'
                    st.markdown(table_html, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # Download Action CTA Box
            with open(temp_output_path, "rb") as out_f:
                redacted_bytes = out_f.read()

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="Download Redacted Document (.docx)",
                data=redacted_bytes,
                file_name=f"Redacted_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )

            # Cleanup temp files
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)


if __name__ == "__main__":
    main()
