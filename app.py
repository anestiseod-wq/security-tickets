import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Facility Ticketing",
    page_icon="🎫",
    layout="wide"
)

# --- SUPABASE INIT ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- SIDEBAR MENU ---
st.sidebar.title("Facility Ticketing")
menu = st.sidebar.radio("Μενού Επιλογών", ["📋 Καταχώρηση Βλάβης", "📊 Ιστορικό & Διαχείριση Tickets"])

# --- VIEW 1: ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ ---
if menu == "📋 Καταχώρηση Βλάβης":
    st.title("📋 Καταχώρηση Νέας Βλάβης / Ticket")
    st.write("Συμπληρώστε τα στοιχεία της βλάβης για άμεση καταγραφή στο σύστημα.")

    with st.form(key="ticket_form", clear_on_submit=True):
        site_display = st.selectbox("Εγκατάσταση / Site *", ["Παπαστράτος", "PMI", "Άλλο"])
        title = st.text_input("Τίτλος Βλάβης / Θέμα *")
        reporter = st.text_input("Όνομα Αναφέροντος / Τμήμα *")

        submit_button = st.form_submit_button(label="🚀 Υποβολή Βλάβης")

    if submit_button:
        if not title or not reporter:
            st.warning("⚠️ Παρακαλώ συμπληρώστε όλα τα πεδία.")
        else:
            # Αντιστοίχιση της ελληνικής επιλογής στην τιμή που δέχεται η βάση
            site_db_value = "PMI" if site_display == "Παπαστράτος" else site_display

            payload = {
                "site": site_db_value,
                "title": title.strip(),
                "reporter": reporter.strip(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            try:
                # Εγγραφή στη βάση Supabase
                res = supabase.table("tickets").insert(payload).execute()
                st.success("✅ Η βλάβη καταχωρήθηκε με επιτυχία!")
                st.balloons()
            except Exception as e:
                # Εμφάνιση του ακριβούς σφάλματος αν αποτύχει
                st.error(f"❌ Σφάλμα βάσης δεδομένων: {e}")

# --- VIEW 2: ΙΣΤΟΡΙΚΟ TICKETS ---
elif menu == "📊 Ιστορικό & Διαχείριση Tickets":
    st.title("📊 Ιστορικό & Διαχείριση Tickets")
    
    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Επαναφορά της ονομασίας "Παπαστράτος" στην προβολή του πίνακα
            if "site" in df.columns:
                df["site"] = df["site"].replace({"PMI": "Παπαστράτος"})
                
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχουν καταγεγραμμένες βλάβες.")
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά την ανάκτηση ιστορικού: {e}")
