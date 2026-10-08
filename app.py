import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Incident & Ticketing Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FULL CUSTOM COLOR PALETTE & CSS STYLING ---
st.markdown("""
    <style>
    :root {
        --bg-primary: #0a192f;
        --bg-secondary: #112240;
        --bg-card: #1d3557;
        --text-primary: #f8f9fa;
        --text-secondary: #8892b0;
        --accent-blue: #0077b6;
        --accent-hover: #023e8a;
        --border-color: #2a4365;
    }

    /* Κύριο φόντο */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* KPI Metric Cards */
    div[data-testid="stMetric"] {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
    }

    /* Κάρτες Φόρμας */
    div[data-testid="stForm"] {
        background-color: var(--bg-secondary) !important;
        border-radius: 12px !important;
        padding: 25px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.4) !important;
    }

    /* Inputs, Selectboxes, Textareas */
    input, textarea, select, div[data-baseweb="select"] {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }

    /* Primary Buttons */
    .stButton>button, .stFormSubmitButton>button {
        background-color: var(--accent-blue) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 24px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0px 4px 12px rgba(0, 119, 182, 0.3) !important;
    }

    .stButton>button:hover, .stFormSubmitButton>button:hover {
        background-color: var(--accent-hover) !important;
        box-shadow: 0px 6px 16px rgba(2, 62, 138, 0.5) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE INITIALIZATION ---
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Σφάλμα σύνδεσης με τα Secrets: {e}")
        st.stop()

supabase = init_supabase()

# --- 4. SESSION STATE FOR NAVIGATION ---
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = "🏠 Αρχική"

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.title("🛡️ Incident Hub")
selected_page = st.sidebar.radio(
    "Μενού Επιλογών",
    ["🏠 Αρχική", "📋 Καταχώρηση Βλάβης", "📊 Ιστορικό & Διαχείριση"],
    index=["🏠 Αρχική", "📋 Καταχώρηση Βλάβης", "📊 Ιστορικό & Διαχείριση"].index(st.session_state.nav_page)
)
st.session_state.nav_page = selected_page

# --- HELPER DATA FETCHING ---
def fetch_data():
    try:
        res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Σφάλμα ανάκτησης: {e}")
        return pd.DataFrame()

df_tickets = fetch_data()

# ==========================================
# VIEW 1: 🏠 ΑΡΧΙΚΗ ΣΕΛΙΔΑ (KPIs & DASHBOARD)
# ==========================================
if st.session_state.nav_page == "🏠 Αρχική":
    st.title("🛡️ Incident & Facility Management Hub")
    st.write("Κεντρικός πίνακας ελέγχου και διαχείρισης βλαβών.")

    st.markdown("---")

    # KPI Metrics Cards
    total_tickets = len(df_tickets) if not df_tickets.empty else 0
    open_tickets = len(df_tickets[df_tickets["status"] == "OPEN"]) if not df_tickets.empty and "status" in df_tickets.columns else total_tickets
    critical_tickets = len(df_tickets[df_tickets["priority"] == "Critical"]) if not df_tickets.empty and "priority" in df_tickets.columns else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("📊 Συνολικά Tickets", total_tickets)
    kpi2.metric("🟡 Ανοιχτές Βλάβες", open_tickets)
    kpi3.metric("🔴 Κρίσιμες Βλάβες", critical_tickets)

    st.markdown("---")
    st.subheader("🚀 Γρήγορες Ενέργειες")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("📋 Καταχώρηση Νέας Βλάβης"):
            st.session_state.nav_page = "📋 Καταχώρηση Βλάβης"
            st.rerun()

    with btn_col2:
        if st.button("📊 Προβολή Ιστορικού & Analytics"):
            st.session_state.nav_page = "📊 Ιστορικό & Διαχείριση"
            st.rerun()

# ==========================================
# VIEW 2: 📋 ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ
# ==========================================
elif st.session_state.nav_page == "📋 Καταχώρηση Βλάβης":
    st.title("📋 Καταχώρηση Νέας Βλάβης")
    st.write("Συμπληρώστε τα στοιχεία της βλάβης για άμεση καταγραφή στο σύστημα.")

    with st.form(key="ticket_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            facility_display = st.selectbox(
                "Εγκατάσταση / Facility *",
                ["Facility A", "Facility B", "General Site"]
            )
            title = st.text_input("Τίτλος Βλάβης / Θέμα *")

        with col2:
            reporter = st.text_input("Κωδικός Αναφέροντος / Τμήμα *")
            priority = st.selectbox(
                "Προτεραιότητα *",
                ["Low", "Medium", "High", "Critical"]
            )

        description = st.text_area("Περιγραφή Βλάβης *", height=120)

        submit_button = st.form_submit_button(label="🚀 Υποβολή Βλάβης")

    if submit_button:
        if not title or not reporter or not description:
            st.warning("⚠️ Παρακαλώ συμπληρώστε όλα τα υποχρεωτικά πεδία.")
        else:
            db_facility_map = {
                "Facility A": "PMI",
                "Facility B": "SITE_B",
                "General Site": "OTHER"
            }
            site_db_value = db_facility_map.get(facility_display, "PMI")

            payload = {
                "site": site_db_value,
                "title": title.strip(),
                "reporter": reporter.strip(),
                "description": description.strip(),
                "priority": priority,
                "created_at": datetime.utcnow().isoformat()
            }
            
            try:
                supabase.table("tickets").insert(payload).execute()
                st.success("✅ Η βλάβη καταχωρήθηκε με επιτυχία στο σύστημα!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Σφάλμα κατά την εγγραφή στη βάση: {e}")

# ==========================================
# VIEW 3: 📊 ΙΣΤΟΡΙΚΟ & ΔΙΑΧΕΙΡΙΣΗ
# ==========================================
elif st.session_state.nav_page == "📊 Ιστορικό & Διαχείριση":
    st.title("📊 Ιστορικό Βλαβών & Incidents")
    
    if df_tickets.empty:
        st.info("Δεν υπάρχουν καταγεγραμμένες βλάβες στη βάση δεδομένων.")
    else:
        # Αντικατάσταση ονομάτων στην προβολή για πλήρη ανωνυμία
        if "site" in df_tickets.columns:
            df_tickets["site"] = df_tickets["site"].replace({
                "PMI": "Facility A",
                "SITE_B": "Facility B",
                "OTHER": "General Site"
            })
            
        st.dataframe(df_tickets, use_container_width=True, hide_index=True)
