import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Facility Ticketing",
    page_icon="🎫",
    layout="wide"
)

# --- 2. SUPABASE INITIALIZATION ---
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

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("Facility Ticketing")
menu = st.sidebar.radio("Μενού Επιλογών", ["📋 Καταχώρηση Βλάβης", "📊 Ιστορικό & Διαχείριση Tickets"])

# --- 4. VIEW 1: ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ ---
if menu == "📋 Καταχώρηση Βλάβης":
    st.title("📋 Καταχώρηση Νέας Βλάβης / Ticket")
    st.write("Συμπληρώστε τα στοιχεία της βλάβης για άμεση καταγραφή στο σύστημα.")

    with st.form(key="ticket_form", clear_on_submit=True):
        site_input = st.selectbox("Εγκατάσταση / Site *", ["Παπαστράτος", "PMI", "Άλλο"])
        title_input = st.text_input("Τίτλος Βλάβης / Θέμα *")
        reporter_input = st.text_input("Όνομα Αναφέροντος / Τμήμα *")

        submit_button = st.form_submit_button(label="🚀 Υποβολή Βλάβης")

    if submit_button:
        if not title_input or not reporter_input:
            st.warning("⚠️ Παρακαλώ συμπληρώστε όλα τα πεδία.")
        else:
            # Μετατροπή της τιμής για να μη χτυπάει το Constraint της βάσης
            db_site = "PMI" if site_input == "Παπαστράτος" else site_input

            payload = {
                "site": db_site,
                "title": title_input.strip(),
                "reporter": reporter_input.strip(),
                "created_at": datetime.utcnow().isoformat()
            }

            try:
                supabase.table("tickets").insert(payload).execute()
                st.success("✅ Η βλάβη καταχωρήθηκε με επιτυχία!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Σφάλμα κατά την εγγραφή στη βάση: {e}")

# --- 5. VIEW 2: ΙΣΤΟΡΙΚΟ TICKETS ---
elif menu == "📊 Ιστορικό & Διαχείριση Tickets":
    st.title("📊 Ιστορικό & Διαχείριση Tickets")

    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Εμφάνιση της ονομασίας όπως την θέλεις στην προβολή
            if "site" in df.columns:
                df["site"] = df["site"].replace({"PMI": "Παπαστράτος"})

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχουν καταγεγραμμένες βλάβες.")
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά την ανάκτηση ιστορικού: {e}")
