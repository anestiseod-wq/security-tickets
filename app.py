import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ticketing & Facility Management",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SUPABASE DATABASE CONNECTION ---
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Σφάλμα σύνδεσης με τα Secrets του Supabase: {e}")
        st.stop()

supabase = init_supabase()

# --- 3. HELPER FUNCTIONS FOR DATABASE OPERATIONS ---
def fetch_tickets():
    """Διαβάζει όλα τα tickets και το ιστορικό από τον πίνακα της βάσης"""
    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά την ανάκτηση ιστορικού: {e}")
        return pd.DataFrame()

def insert_ticket(title, description, site, priority, reporter):
    """Καταχωρεί μια νέα βλάβη στη βάση δεδομένων"""
    payload = {
        "title": title.strip(),
        "description": description.strip(),
        "site": site.strip(),  # 'Παπαστράτος' ή 'PMI'
        "priority": priority,
        "reporter": reporter.strip(),
        "status": "OPEN",
        "created_at": datetime.utcnow().isoformat()
    }
    try:
        response = supabase.table("tickets").insert(payload).execute()
        return True, response
    except Exception as e:
        return False, str(e)

# --- 4. NAVIGATION & SIDEBAR ---
st.sidebar.title("🎫 Facility Ticketing")
menu = st.sidebar.radio("Μενού Επιλογών", ["📋 Καταχώρηση Βλάβης", "📊 Ιστορικό & Διαχείριση Tickets"])

# --- 5. VIEW 1: ΚΑΤΑΧΩΡΗΣΗ ΝΕΑΣ ΒΛΑΒΗΣ ---
if menu == "📋 Καταχώρηση Βλάβης":
    st.title("📋 Καταχώρηση Νέας Βλάβης / Ticket")
    st.write("Συμπληρώστε τα στοιχεία της βλάβης για άμεση καταγραφή στο σύστημα.")

    with st.form(key="ticket_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            site_option = st.selectbox(
                "Εγκατάσταση / Site *",
                ["Παπαστράτος", "PMI", "Άλλο"]
            )
            title = st.text_input("Τίτλος Βλάβης / Θέμα *")
            reporter = st.text_input("Όνομα Αναφέροντος / Τμήμα *")

        with col2:
            priority = st.selectbox(
                "Προτεραιότητα *",
                ["Χαμηλή (Low)", "Μεσαία (Medium)", "Υψηλή (High)", "Κρίσιμη (Critical)"]
            )
            description = st.text_area("Περιγραφή Βλάβης / Λεπτομέρειες *", height=120)

        submit_button = st.form_submit_button(label="🚀 Υποβολή Βλάβης")

    if submit_button:
        # Έλεγχος υποχρεωτικών πεδίων
        if not title or not description or not reporter:
            st.warning("⚠️ Παρακαλώ συμπληρώστε όλα τα υποχρεωτικά πεδία με αστερίσκο (*).")
        else:
            success, result = insert_ticket(title, description, site_option, priority, reporter)
            if success:
                st.success(f"✅ Η βλάβη καταχωρήθηκε με επιτυχία στη βάση! (Site: {site_option})")
                st.balloons()
            else:
                st.error(f"❌ Αποτυχία εγγραφής στη βάση Supabase: {result}")

# --- 6. VIEW 2: ΙΣΤΟΡΙΚΟ & ΔΙΑΧΕΙΡΙΣΗ TICKETS ---
elif menu == "📊 Ιστορικό & Διαχείριση Tickets":
    st.title("📊 Ιστορικό & Κατάσταση Βλαβών")
    st.write("Πλήρες ιστορικό καταγεγραμμένων βλαβών από τη βάση δεδομένων.")

    df_tickets = fetch_tickets()

    if df_tickets.empty:
        st.info("ℹ️ Δεν βρέθηκαν καταχωρημένα tickets στη βάση δεδομένων.")
    else:
        # Φίλτρα προβολής
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            site_filter = st.multiselect("Φίλτρο ανά Εγκατάσταση:", options=df_tickets["site"].unique(), default=df_tickets["site"].unique())
        with col_f2:
            status_filter = st.multiselect("Φίλτρο ανά Κατάσταση:", options=df_tickets["status"].unique(), default=df_tickets["status"].unique())

        # Εφαρμογή φίλτρων
        filtered_df = df_tickets[
            (df_tickets["site"].isin(site_filter)) & 
            (df_tickets["status"].isin(status_filter))
        ]

        # Προβολή πίνακα
        st.dataframe(
            filtered_df[[
                "id", "created_at", "site", "title", "reporter", "priority", "status", "description"
            ]],
            use_container_width=True,
            hide_index=True
        )

        # Δυνατότητα Export σε CSV
        csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Εξαγωγή Ιστορικού σε CSV",
            data=csv_data,
            file_name=f"tickets_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
