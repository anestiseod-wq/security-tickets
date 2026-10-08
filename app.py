import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Incident & Ticketing Management",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FULL CUSTOM COLOR PALETTE & CSS STYLING ---
st.markdown("""
    <style>
    /* Κύρια παλέτα χρωμάτων */
    :root {
        --bg-primary: #0a192f;
        --bg-secondary: #112240;
        --bg-card: #1d3557;
        --text-primary: #f8f9fa;
        --text-secondary: #8892b0;
        --accent-blue: #0077b6;
        --accent-hover: #023e8a;
        --border-color: #2a4365;
        --success-color: #2a9d8f;
        --danger-color: #e63946;
    }

    /* Φόντο Εφαρμογής */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* Κάρτες και Φόρμες (Form Styling) */
    div[data-testid="stForm"] {
        background-color: var(--bg-secondary) !important;
        border-radius: 12px !important;
        padding: 30px !important;
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

    /* Form Labels & Text Header */
    label, p, h1, h2, h3, h4, span {
        color: var(--text-primary) !important;
    }

    /* Primary Buttons Styling */
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
        transform: translateY(-1px);
    }

    /* Dataframe / Table Styling */
    [data-testid="stDataFrame"] {
        background-color: var(--bg-secondary) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
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

# --- 4. NAVIGATION SIDEBAR ---
st.sidebar.title("🛡️ Incident Hub")
menu = st.sidebar.radio("Μενού Επιλογών", ["📋 Καταχώρηση Βλάβης", "📊 Ιστορικό & Διαχείριση"])

# --- 5. VIEW 1: ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ (ANONYMIZED) ---
if menu == "📋 Καταχώρηση Βλάβης":
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
            # Mapping των ανώνυμων επιλογών στις τιμές που περιμένει η βάση
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

# --- 6. VIEW 2: ΙΣΤΟΡΙΚΟ (ANONYMIZED DISPLAY) ---
elif menu == "📊 Ιστορικό & Διαχείριση":
    st.title("📊 Ιστορικό Βλαβών & Incidents")
    
    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Αντικατάσταση ονομάτων στην προβολή για πλήρη ανωνυμία
            if "site" in df.columns:
                df["site"] = df["site"].replace({
                    "PMI": "Facility A",
                    "SITE_B": "Facility B",
                    "OTHER": "General Site"
                })
                
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχουν καταγεγραμμένες βλάβες.")
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά την ανάκτηση ιστορικού: {e}")
