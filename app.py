import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE CONNECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="PMI - Security Maintenance Hub (DEMO)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    
    .audit-box {
        background-color: #1e293b;
        border: 1px solid #475569;
        padding: 15px;
        border-radius: 10px;
        color: #f8fafc;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }

    /* Περιορισμός μεγέθους φωτογραφίας */
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

# ---------------------------------------------------------
# 3. DATA RETRIEVAL
# ---------------------------------------------------------
def fetch_data():
    try:
        tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

df_tickets = fetch_data()
HOURLY_RATE = 25.0

if not df_tickets.empty:
    df_tickets["created_dt"] = pd.to_datetime(df_tickets["created_at"], errors="coerce").dt.tz_localize(None)
    df_tickets["Ημερομηνία_Str"] = df_tickets["created_dt"].dt.strftime('%d/%m/%Y')
    df_tickets["Έτος"] = df_tickets["created_dt"].dt.year.fillna(datetime.now().year).astype(int)
    df_tickets["Μήνας_Num"] = df_tickets["created_dt"].dt.month.fillna(datetime.now().month).astype(int)
    
    month_names = {1: "Ιανουάριος", 2: "Φεβρουάριος", 3: "Μάρτιος", 4: "Απρίλιος", 5: "Μάιος", 6: "Ιούνιος",
                   7: "Ιούλιος", 8: "Αύγουστος", 9: "Σεπτέμβριος", 10: "Οκτώβριος", 11: "Νοέμβριος", 12: "Δεκέμβριος"}
    df_tickets["Μήνας"] = df_tickets["Μήνας_Num"].map(month_names)

    if "resolution_time_hrs" in df_tickets.columns:
        df_tickets["resolution_time_hrs"] = pd.to_numeric(df_tickets["resolution_time_hrs"], errors="coerce").fillna(0.0)

# ---------------------------------------------------------
# 4. SESSION STATE
# ---------------------------------------------------------
if "view_mode" not in st.session_state: st.session_state.view_mode = "home"
if "active_ticket_id" not in st.session_state: st.session_state.active_ticket_id = None
if "success_msg" not in st.session_state: st.session_state.success_msg = None

# ---------------------------------------------------------
# 5. HEADER (WITH LIVE PULSE & DEMO BADGE)
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <span class="demo-badge">🧪 DEMO CONCEPT / PROPOSAL MODE</span>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Security Maintenance Hub — Papastratos (PMI)
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 600;">
                    Πρόταση Συστήματος Διαχείρισης Βλαβών, Ιστορικού & KPIs Συντήρησης
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.85); padding: 10px 18px; border-radius: 12px; border: 1px solid #10b981;">
                <span class="pulse-dot"></span>
                <span style="color: #10b981; font-weight: 800; font-size: 0.95rem;">SYSTEM ACTIVE (LIVE)</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.success_msg:
    st.markdown(f'<div class="success-banner">{st.session_state.success_msg}</div>', unsafe_allow_html=True)
    st.session_state.success_msg = None

# ---------------------------------------------------------
# 6. ΚΟΥΜΠΙΑ ΠΛΟΗΓΗΣΗΣ
# ---------------------------------------------------------
nav_c1, nav_c2, nav_c3 = st.columns(3)
with nav_c1:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("🏠 Αρχική Σελίδα & KPIs"):
        st.session_state.view_mode = "home"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_c2:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("➕ Νέα Καταχώρηση Βλάβης"):
        st.session_state.view_mode = "new_ticket"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_c3:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("📋 Λίστα & Ιστορικό Βλαβών"):
        st.session_state.view_mode = "list_tickets"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. ΟΘΟΝΗ 1: ΑΡΧΙΚΗ & ΣΥΝΟΛΙΚΑ KPIs
# ---------------------------------------------------------
if st.session_state.view_mode == "home":
    st.subheader("📊 Κεντρικά Σύνολα, KPIs & Κόστη (Demo Overview)")

    if not df_tickets.empty:
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            years_available = ["Όλα τα Έτη"] + sorted(list(df_tickets["Έτος"].unique()), reverse=True)
            sel_year = st.selectbox("📅 Επιλογή Έτους:", years_available)
        with f_col2:
            sel_month = st.selectbox("📆 Επιλογή Μήνα:", ["Όλοι οι Μήνες"] + list(month_names.values()))

        filtered_home_df = df_tickets.copy()
        if sel_year != "Όλα τα Έτη":
            filtered_home_df = filtered_home_df[filtered_home_df["Έτος"] == int(sel_year)]
        if sel_month != "Όλοι οι Μήνες":
            filtered_home_df = filtered_home_df[filtered_home_df["Μήνας"] == sel_month]

        tot_tck = len(filtered_home_df)
        op_tck = len(filtered_home_df[filtered_home_df["status"] == "Open"])
        pend_tck = len(filtered_home_df[filtered_home_df["status"] == "Pending"])
        cl_tck = len(filtered_home_df[filtered_home_df["status"] == "Closed"])
        
        tot_hrs = float(filtered_home_df["resolution_time_hrs"].sum()) if "resolution_time_hrs" in filtered_home_df.columns else 0.0
        tot_labor_cost = tot_hrs * HOURLY_RATE

        closed_df = filtered_home_df[filtered_home_df["status"] == "Closed"].copy()
        avg_days = 0.0
        if not closed_df.empty:
            closed_df["c_dt"] = pd.to_datetime(closed_df["created_at"], errors="coerce").dt.tz_localize(None)
            closed_df["dur_days"] = (datetime.now() - closed_df["c_dt"]).dt.total_seconds() / 86400.0
            avg_days = max(0.0, float(closed_df["dur_days"].mean()))

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Σύνολο Βλαβών", tot_tck)
        k2.metric("🔴 Open", op_tck)
        k3.metric("🟡 Pending", pend_tck)
        k4.metric("🟢 Closed", cl_tck)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("⏱️ Σύνολο Ωρών Εργασίας", f"{tot_hrs:.1f} hrs")
        c2.metric("💰 Σύνολο Κόστους Εργασίας (€25/h)", f"€{tot_labor_cost:,.2f}")
        c3.metric("📅 Μέσος Χρόνος Αποκατάστασης (MTTR)", f"{avg_days:.1f} ημέρες")

        st.markdown("---")
        st.subheader("📊 Ανάλυση Βλαβών & Ωρών ανά Τμήμα")
        if "category" in filtered_home_df.columns:
            dept_summary = filtered_home_df.groupby("category").agg(
                Βλάβες=("ticket_id", "count"),
                Σύνολο_Ωρών=("resolution_time_hrs", "sum")
            ).reset_index()
            st.dataframe(dept_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένες βλάβες στη βάση.")

# ---------------------------------------------------------
# 8. ΟΘΟΝΗ 2: ΝΕΑ ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ
# ---------------------------------------------------------
elif st.session_state.view_mode == "new_ticket":
    st.subheader("📝 Φόρμα Καταχώρησης Νέας Βλάβης")
    
    with st.form("new_ticket_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tck_id = st.text_input("Κωδικός Ticket", value=f"TCK-{datetime.now().strftime('%m%d-%H%M')}")
            creator_tech = st.text_input("👤 Ο
