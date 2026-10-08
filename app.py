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
    page_title="Demo Ticketing Site - Security Hub",
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
    
    parts = re.split(r'(?=\[\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\])', str(raw_text).strip())
    entries = [p.strip() for p in parts if p.strip()]
    
    def extract_dt(text):
        match = re.search(r'\[(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\]', text)
        if match:
            try:
                return datetime.strptime(match.group(1), '%d/%m/%Y %H:%M')
            except Exception:
                return datetime.min
        return datetime.min

    entries.sort(key=extract_dt, reverse=True)
    
    html_out = ""
    for idx, entry in enumerate(entries):
        css_class = "audit-entry-card-newest" if idx == 0 else "audit-entry-card"
        html_out += f'<div class="{css_class}">{entry}</div>'
    
    return html_out

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
                <span class="demo-badge">🧪 DEMO CONCEPT / PROPOSAL SITE</span>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Security Operations & Maintenance Hub
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 600;">
                    Πρόταση Сυστήματος Διαχείρισης Βλαβών (Ticketing), Ιστορικού & KPIs
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
            creator_tech = st.text_input("👤 Ονοματεπώνυμο Χρήστη / Τεχνικού", value="Ανέστης Θεοδωρίδης")
            user_role = st.selectbox("🎭 Ρόλος / Ειδικότητα", ["Security Systems Admin", "Technical Expert", "Security Officer", "Shift Supervisor", "External Contractor"])
            category = st.selectbox("Τμήμα / Κατηγορία", ["CCTV (Κάμερες)", "ACS (Access Control / Τουρνικέ)", "Fire Alarm (Πυρανίχνευση)", "Network / PoE / Fiber", "Άλλο"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Είσοδος Τουρνικέ")

        with f2:
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. Cam 20 / Reader CR.08")
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "Pending", "Closed"])
            duration_hrs = st.number_input("⏱️ Αρχικές Ώρες Εργασίας (hrs)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
            materials = st.text_area("🛠️ Περιγραφή Υλικών / Ανταλλακτικών", placeholder="π.χ. 1x PoE Injector, 10m UTP Cat6")

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή της βλάβης...")

        st.markdown("##### 📁 Επιλογή Αρχείου Φωτογραφίας (Προαιρετικό)")
        upload_photo = st.file_uploader("Μεταφόρτωση Εικόνας", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("💾 Αποθήκευση Βλάβης στη Βάση"):
            photo_b64 = get_b64_img(upload_photo)
            
            now_stamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            role_str = f"[{user_role}]" if user_role else ""
            creator_prefix = f"[{now_stamp} - Καταχώρηση: {creator_tech} {role_str}]\n" if creator_tech.strip() else f"[{now_stamp} - Νέα Καταχώρηση]\n"
            
            insert_payload = {
                "ticket_id": tck_id,
                "category": category,
                "building_area": building_area,
                "device_asset": device_asset,
                "priority": priority,
                "status": status,
                "description": f"{creator_prefix}{description}",
                "materials_used": materials if materials else "Καμία χρήση υλικών",
                "resolution_time_hrs": float(duration_hrs)
            }
            if photo_b64:
                insert_payload["photo_url"] = photo_b64
            
            try:
                supabase.table("tickets").insert(insert_payload).execute()
                st.session_state.success_msg = f"✅ Η βλάβη **{tck_id}** καταχωρήθηκε επιτυχώς!"
                st.session_state.view_mode = "home"
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Σφάλμα καταχώρησης: {e}")

# ---------------------------------------------------------
# 9. ΟΘΟΝΗ 3: ΛΙΣΤΑ ΒΛΑΒΩΝ ΑΝΑ ΗΜΕΡΟΜΗΝΙΑ & DETAILS
# ---------------------------------------------------------
elif st.session_state.view_mode == "list_tickets":
    
    if st.session_state.active_ticket_id and not df_tickets.empty:
        selected_row = df_tickets[df_tickets["ticket_id"] == st.session_state.active_ticket_id]
        
        if not selected_row.empty:
            row = selected_row.iloc[0]
            
            if st.button("⬅️ Επιστροφή στη Λίστα Όλων των Βλαβών"):
                st.session_state.active_ticket_id = None
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            badge_color = "#ef4444" if row['status'] == "Open" else ("#f59e0b" if row['status'] == "Pending" else "#10b981")
            
            c_dt = pd.to_datetime(row.get('created_at'), errors='coerce')
            if pd.notnull(c_dt):
                c_dt = c_dt.tz_localize(None)
                open_days = max(0, (datetime.now() - c_dt).days)
            else:
                open_days = 0

            lab_cost = float(row.get('resolution_time_hrs', 0.0) or 0.0) * HOURLY_RATE

            st.markdown(f"""
            <div class="full-card" style="border-left-color: {badge_color};">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <h2 style="margin:0; color:#38bdf8;">🎫 Ticket: {row.get('ticket_id', '')}</h2>
                    <span style="background-color:{badge_color}; color:#000; font-weight:800; padding:6px 14px; border-radius:20px; font-size:1rem;">
                        {row.get('status', 'Open')}
                    </span>
                </div>
                <hr style="border-color:#334155; margin:15px 0;">
                <p><b>📍 Τμήμα:</b> {row.get('category', '')} | <b>🏢 Περιοχή:</b> {row.get('building_area', '')} | <b>📹 Asset:</b> {row.get('device_asset', '')}</p>
                <p><b>🚨 Προτεραιότητα:</b> {row.get('priority', '')} | <b>⏱️ Ώρες Εργασίας:</b> {row.get('resolution_time_hrs', 0.0)} hrs (€{lab_cost:,.2f}) | <b>📅 Ανοιχτό για:</b> {open_days} ημέρες</p>
                <p><b>🛠️ Υλικά / Ανταλλακτικά:</b> {row.get('materials_used', 'Καμία χρήση υλικών')}</p>
            </div>
            """, unsafe_allow_html=True)

            if pd.notnull(row.get('photo_url')) and str(row.get('photo_url')).startswith('data:image'):
                st.markdown("##### 📷 Φωτογραφία Βλάβης / Υλικού")
                st.markdown(f'<div class="small-photo-container"><img src="{row.get("photo_url")}"/></div><br>', unsafe_allow_html=True)

            st.subheader("📜 Ιστορικό Ενεργειών & Ενημερώσεων")
            formatted_history = format_audit_trail(row.get('description', ''))
            st.markdown(formatted_history, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📝 Προσθήκη Νέας Ενημέρωσης / Αλλαγή Κατάστασης")
            
            with st.form("update_ticket_form"):
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    update_tech = st.text_input("👤 Ονοματεπώνυμο Τεχνικού / Χρήστη", value="Ανέστης Θεοδωρίδης")
                    update_role = st.selectbox("🎭 Ρόλος", ["Security Systems Admin", "Technical Expert", "Security Officer", "Shift Supervisor", "External Contractor"])
                    new_status = st.selectbox("Ενημέρωση Κατάστασης", ["Open", "Pending", "Closed"], index=["Open", "Pending", "Closed"].index(row.get('status', 'Open')) if row.get('status') in ["Open", "Pending", "Closed"] else 0)

                with u_col2:
                    add_hrs = st.number_input("⏱️ Επιπλέον Ώρες Εργασίας", min_value=0.0, max_value=50.0, value=0.0, step=0.5)
                    add_materials = st.text_input("🛠️ Επιπλέον Υλικά", placeholder="π.χ. +1x Connector BNC")

                new_note = st.text_area("💬 Νέα Ενέργεια / Σχόλιο", placeholder="Γράψτε τη νέα ενημέρωση...")
                
                if st.form_submit_button("🔄 Ενημέρωση Ticket στη Βάση"):
                    if new_note.strip():
                        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
                        r_str = f"[{update_role}]" if update_role else ""
                        entry_header = f"[{now_str} - Ενημέρωση: {update_tech} {r_str}]"
                        full_entry = f"{entry_header}\n{new_note.strip()}"
                        
                        existing_desc = str(row.get('description', '')) if pd.notnull(row.get('description')) else ""
                        updated_desc = f"{full_entry}\n\n{existing_desc}" if existing_desc.strip() else full_entry

                        curr_hrs = float(row.get('resolution_time_hrs', 0.0) or 0.0)
                        total_hrs = curr_hrs + float(add_hrs)

                        curr_mat = str(row.get('materials_used', '')) if pd.notnull(row.get('materials_used')) else ""
                        updated_mat = f"{curr_mat} | {add_materials.strip()}" if add_materials.strip() and curr_mat else (add_materials.strip() or curr_mat)

                        update_payload = {
                            "status": new_status,
                            "description": updated_desc,
                            "resolution_time_hrs": total_hrs,
                            "materials_used": updated_mat
                        }

                        try:
                            supabase.table("tickets").update(update_payload).eq("ticket_id", row.get('ticket_id')).execute()
                            st.session_state.success_msg = f"✅ Το ticket **{row.get('ticket_id')}** ενημερώθηκε επιτυχώς!"
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ Σφάλμα ενημέρωσης: {e}")
                    else:
                        st.warning("⚠️ Παρακαλώ γράψτε ένα σχόλιο/ενέργεια για την ενημέρωση.")

    else:
        st.subheader("📋 Λίστα & Ιστορικό Όλων των Βλαβών")
        
        if not df_tickets.empty:
            grouped = df_tickets.groupby("Ημερομηνία_Str")
            
            for date_str, group in grouped:
                st.markdown(f'<div class="date-header">📅 Ημερομηνία: {date_str} ({len(group)} βλάβες)</div>', unsafe_allow_html=True)
                
                for idx, row in group.iterrows():
                    st_color = "#ef4444" if row['status'] == "Open" else ("#f59e0b" if row['status'] == "Pending" else "#10b981")
                    
                    c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
                    c1.markdown(f"**🎫 {row.get('ticket_id', '')}**")
                    c2.markdown(f"📍 {row.get('category', '')} - {row.get('building_area', '')}")
                    c3.markdown(f'<span style="color:{st_color}; font-weight:800;">● {row.get("status", "Open")}</span>', unsafe_allow_html=True)
                    
                    with c4:
                        if st.button("🔍 Προβολή", key=f"btn_{row.get('ticket_id')}_{idx}"):
                            st.session_state.active_ticket_id = row.get('ticket_id')
                            st.rerun()
                    st.markdown("<hr style='border-color:#1e293b; margin:6px 0;'>", unsafe_allow_html=True)
        else:
            st.info("Δεν υπάρχουν καταχωρημένες βλάβες στη βάση.")
