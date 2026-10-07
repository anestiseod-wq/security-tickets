import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import re
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE CONNECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Demo Ticketing Site - Security Maintenance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔒 ΣΥΣΤΗΜΑ ΑΣΦΑΛΕΙΑΣ / ΚΛΕΙΔΩΜΑ ΜΕ PIN
APP_PIN = "2020"  # <-- Κωδικός πρόσβασης

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .stApp { background-color: #0b1329; color: #f8fafc; }
        div[data-testid="stForm"] { background-color: #1e293b; border: 1px solid #38bdf8; padding: 30px; border-radius: 16px; max-width: 450px; margin: 50px auto; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>🛡️ Security Maintenance Hub</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Εισάγετε τον κωδικό πρόσβασης για είσοδο στο Demo Site:</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        user_pin = st.text_input("🔑 Κωδικός Πρόσβασης (PIN):", type="password")
        submit_pin = st.form_submit_button("🔓 Είσοδος στο Σύστημα")
        
        if submit_pin:
            if user_pin == APP_PIN:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Λανθασμένος κωδικός πρόσβασης.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception:
    st.error("⚠️ Σφάλμα σύνδεσης με τη βάση Supabase. Ελέγξτε τα Secrets στο Streamlit Cloud.")
    st.stop()

# ---------------------------------------------------------
# 2. MODERN HIGH-CONTRAST THEME & LIVE PULSE ANIMATION (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }
    
    .stApp { 
        background-color: #0b1329; 
        color: #f8fafc; 
        font-family: 'Inter', system-ui, -apple-system, sans-serif; 
    }
    
    .pmi-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #0284c7 100%);
        padding: 22px 26px;
        border-radius: 16px;
        border: 1px solid #38bdf8;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
    }

    .demo-badge {
        background-color: #f59e0b;
        color: #000000;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.5px;
        display: inline-block;
        margin-bottom: 6px;
    }
    
    /* Live Pulse LED Animation */
    .pulse-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 1.6s infinite;
        margin-right: 6px;
        vertical-align: middle;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px !important;
    }
    
    label { color: #e2e8f0 !important; font-weight: 700 !important; font-size: 0.95rem !important; }

    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 16px; 
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; font-size: 0.9rem; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 1.6rem; }

    .big-nav-btn button {
        height: 60px !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 12px 20px !important;
    }
    
    .full-card {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-left: 6px solid #38bdf8;
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 20px;
        width: 100%;
    }

    .date-header {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-left: 4px solid #0284c7;
        padding: 8px 14px;
        border-radius: 8px;
        margin-top: 15px;
        margin-bottom: 10px;
        color: #38bdf8;
        font-weight: 700;
        font-size: 1rem;
    }

    .success-banner {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        padding: 16px;
        border-radius: 12px;
        color: #6ee7b7;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .audit-entry-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: #f8fafc;
        white-space: pre-wrap;
        font-family: inherit;
    }

    .audit-entry-card-newest {
        background-color: #0f172a;
        border: 1px solid #0284c7;
        border-left: 5px solid #10b981;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 12px;
        color: #f8fafc;
        white-space: pre-wrap;
        font-family: inherit;
    }

    .small-photo-container img {
        max-width: 380px !important;
        max-height: 300px !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
        object-fit: cover !important;
    }
    </style>
""", unsafe_allow_html=True)

def get_b64_img(file):
    if file is not None:
        try:
            b_data = file.getvalue()
            if not b_data: return None
            encoded = base64.b64encode(b_data).decode()
            mime = getattr(file, 'type', 'image/jpeg') or 'image/jpeg'
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return None
    return None

def format_audit_trail(raw_text):
    if not raw_text or not str(raw_text).strip():
        return '<div class="audit-entry-card">Δεν υπάρχει καταγεγραμμένο ιστορικό.</div>'
    
    parts = re.split(r'(?=\[\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', str(raw_text).strip())
    entries = [p.strip() for p in
