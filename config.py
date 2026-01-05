"""
設定・定数・CSS
"""
import streamlit as st
import time


def log_perf(label: str):
    """パフォーマンスログを出力"""
    if 'perf_start' not in st.session_state:
        st.session_state.perf_start = time.time()
    elapsed = (time.time() - st.session_state.perf_start) * 1000
    print(f"[PERF] {label}: {elapsed:.1f}ms")


# --- API Settings ---
DEFAULT_API_KEY = "AIzaSyASXSSBXpcmZHI6l33plPg5uXJo9iQD0VY"
GEMINI_MODEL = "gemini-2.0-flash-exp"


# --- LocalStorage Keys ---
STORAGE_KEY = "audio_ai_assistant_history"
SCRIPT_STORAGE_KEY = "audio_ai_assistant_saved_scripts"
TRANSCRIPTION_STORAGE_KEY = "voice_transcriptions"
SETTINGS_STORAGE_KEY = "audio_ai_assistant_settings"


# --- Default Settings ---
def get_default_settings():
    """デフォルト設定を返す"""
    return {
        "broadcaster_name": "",
        "target_audience": "",
        "speaking_style": "親しみやすく",
        "episodes": []
    }


# --- CSS Styles ---
CUSTOM_CSS = """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Font display swap for faster TTI */
    * { font-display: swap; }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #12121a 100%);
        color: #f0f0f5;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    
    /* Headers */
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }
    
    h2, h3 {
        font-weight: 600 !important;
        color: #e8e8ed !important;
        letter-spacing: -0.01em;
    }
    
    /* Subtitle text */
    .stMarkdown p {
        color: #9898a6;
        line-height: 1.6;
    }
    
    /* Input Fields */
    .stTextArea textarea, .stTextInput input {
        background-color: #18181f !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #2a2a35 !important;
        padding: 14px !important;
        font-size: 15px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #18181f;
        border-radius: 12px;
        border: 2px dashed #2a2a35;
        padding: 1.5rem;
    }
    
    .stFileUploader:hover {
        border-color: #6366f1;
    }
    
    /* Primary Buttons */
    .stButton > button[kind="primary"], 
    .stButton > button:not([kind="secondary"]) {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        color: white !important;
        padding: 12px 24px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind="secondary"]):hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
    }
    
    /* Secondary Buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #3a3a45 !important;
        color: #9898a6 !important;
        padding: 10px 20px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #1f1f28 !important;
        border-color: #6366f1 !important;
        color: #e8e8ed !important;
    }
    
    /* Link buttons */
    .stLinkButton a {
        background: transparent !important;
        border: 1px solid #3a3a45 !important;
        color: #9898a6 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stLinkButton a:hover {
        background: #1f1f28 !important;
        border-color: #6366f1 !important;
        color: #ffffff !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #18181f;
        padding: 4px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 10px 16px;
        color: #9898a6;
        font-weight: 500;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #18181f !important;
        border-radius: 10px !important;
        color: #e8e8ed !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #18181f !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Success/Info/Error messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12121a !important;
        border-right: 1px solid #1f1f28;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 1.1rem !important;
        color: #e8e8ed !important;
        margin-bottom: 1rem !important;
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background: #1f1f28 !important;
        border: 1px solid #2a2a35 !important;
        color: #e8e8ed !important;
        font-size: 13px !important;
        padding: 10px 12px !important;
        box-shadow: none !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #2a2a35 !important;
        border-color: #6366f1 !important;
    }
    
    /* Divider */
    hr {
        border-color: #2a2a35 !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Audio player */
    audio {
        width: 100%;
        border-radius: 10px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #6366f1 !important;
    }
    
    /* Storage badge */
    .storage-badge {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Caption text */
    .stCaption {
        color: #6b6b78 !important;
    }
</style>
"""


def apply_custom_css():
    """カスタムCSSを適用"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
