import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE CONNECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="PMI - Security Maintenance Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
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
# 2. MODERN HIGH-CONTRAST INDUSTRIAL THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { 
        background-color: #0b1329; 
        color: #f8fafc; 
        font-family: 'Inter', system-ui, -apple-system, sans-serif; 
    }
    
    .pmi-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #0284c7 100%);
        padding: 22px 28px;
        border-radius: 16px;
        border: 1px solid #38bdf8;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
    }
    
    /* Input Fields & Text Areas */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    
    label { 
        color: #e2e8f0 !important; 
        font-weight: 700 !important; 
        font-size: 0.92rem !important;
        margin-bottom: 4px !important;
    }

    /* Metric Dashboard Cards */
    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 16px; 
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 1.7rem; }

    /* Action Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 10px 18px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #075985 100%) !important;
        border-color: #7dd3fc !important;
    }

    /* Expander / Accordion Styling */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stForm"] { 
        background-color: #1e293b; 
        border: 1px solid #334155; 
        padding: 22px; 
        border-radius: 14px; 
    }
    </style>
""", unsafe_allow_html=True)

# Helper: Μετατροπή Εικόνας σε Base64 για Απευθείας Ασφαλή Προβολή
def file_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        mime_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'image/jpeg'
        return f"data:{mime_type};base64,{base64_str}"
    return None

# Helper: Upload στο Supabase Storage (με fallback)
def save_photo(file, ticket_id):
    if file is not None:
        try:
            b64_img = file_to_base64(file)
            file_ext = file.name.split('.')[-1] if hasattr(file, 'name') and file.name else 'jpg'
            file_path = f"{ticket_id}_{datetime.now().strftime('%M%S')}.{file_ext}"
            
            supabase.storage.from_("ticket-photos").upload(
                file_path, file.getvalue(), file_options={"content-type": f"image/{file_ext}"}
            )
            pub_url = supabase.storage.from_("ticket-photos").get_public_url(file_path)
            return pub_url if pub_url else b64_img
        except Exception:
            return file_to_base64(file)
    return None

# ---------------------------------------------------------
# 3. DATA RETRIEVAL
# ---------------------------------------------------------
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

# ---------------------------------------------------------
# 4. HEADER & KPIs
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify- justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Papastratos (PMI) - Security Systems & Maintenance
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 600;">
                    Διαδραστικός Πίνακας Βλαβών, Τεχνικών, Υλικών & Φωτογραφιών
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.8); padding: 8px 16px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800;">● SYSTEM ACTIVE</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# KPIs
total_tck = len(df_tickets)
open_tck = len(df_tickets[df_tickets["status"] == "Open"]) if not df_tickets.empty else 0
pending_tck = len(df_tickets[df_tickets["status"] == "Pending"]) if not df_tickets.empty else 0
closed_tck = len(df_tickets[df_tickets["status"] == "Closed"]) if not df_tickets.empty else 0
total_hours = df_tickets["resolution_time_hrs"].sum() if not df_tickets.empty and "resolution_time_hrs" in df_tickets.columns else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Σύνολο", total_tck)
k2.metric("🔴 Open", open_tck)
k3.metric("🟡 Pending", pending_tck)
k4.metric("🟢 Closed", closed_tck)
k5.metric("⏱️ Ώρες", f"{total_hours:.1f}h")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 1. Καταχώρηση Νέας Βλάβης", "📋 2. Κάρτες Βλαβών & Ενημέρωση", "📊 3. Αναλυτικό Ιστορικό"])

# TAB 1: NEW TICKET FORM
with tab1:
    st.subheader("📝 Νέα Αναφορά Βλάβης / Συντήρησης")
    
    with st.form("new_ticket_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tck_id = st.text_input("Κωδικός Ticket", value=f"TCK-{datetime.now().strftime('%m%d-%H%M')}")
            creator_tech = st.text_input("👤 Τεχνικός / Χειριστής Καταχώρησης", placeholder="π.χ. Ανέστης Θεοδωρίδης")
            category = st.selectbox("Κατηγορία Συστήματος", ["CCTV (Κάμερες)", "ACS (Access Control / Τουρνικέ)", "Fire Alarm (Πυρανίχνευση)", "Network / PoE / Fiber", "Άλλο"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Είσοδος Τουρνικέ DR_116")
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. Cam 20 / Reader CR.08L0.01.01")

        with f2:
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "Pending", "Closed"])
            duration_hrs = st.number_input("⏱️ Αρχικές Ώρες Εργασίας (hrs)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
            materials = st.text_area("🛠️ Υλικά / Ανταλλακτικά", placeholder="π.χ. 1x PoE Injector, 10m UTP Cat6, 2x RJ45")

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή...")
        
        st.markdown("##### 📸 Φωτογραφία Βλάβης")
        img_file = st.file_uploader("Επιλέξτε ή τραβήξτε φωτογραφία", type=["jpg", "jpeg", "png"], key="new_img")

        if st.form_submit_button("➕ Καταχώρηση Νέας Βλάβης στη Βάση"):
            photo_data = save_photo(img_file, tck_id)
            creator_prefix = f"[Καταχώρηση: {creator_tech}]\n" if creator_tech.strip() else ""
            
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
            if photo_data:
                insert_payload["photo_url"] = photo_data
                
            supabase.table("tickets").insert(insert_payload).execute()
            st.success(f"✅ Η βλάβη **{tck_id}** καταχωρήθηκε επιτυχώς!")
            st.rerun()

# TAB 2: INTERACTIVE CARDS & DIRECT EDIT
with tab2:
    st.subheader("📋 Διαδραστικός Πίνακας Βλαβών (Click-to-Open Cards)")
    
    if not df_tickets.empty:
        c_filter, c_search = st.columns([1, 2])
        with c_filter:
            status_filter = st.selectbox("Φιλτράρισμα:", ["Όλες οι Βλάβες", "🔴 Ανοιχτές (Open & Pending)", "🟢 Ολοκληρωμένες (Closed)"])
        with c_search:
            search_txt = st.text_input("🔍 Αναζήτηση σε όλες τις βλάβες:", placeholder="Αναζήτηση με κωδικό, κτίριο, συσκευή...")

        display_cards = df_tickets.copy()
        if status_filter == "🔴 Ανοιχτές (Open & Pending)":
            display_cards = display_cards[display_cards["status"] != "Closed"]
        elif status_filter == "🟢 Ολοκληρωμένες (Closed)":
            display_cards = display_cards[display_cards["status"] == "Closed"]

        if search_txt:
            display_cards = display_cards[
                display_cards["ticket_id"].str.contains(search_txt, case=False, na=False) |
                display_cards["building_area"].str.contains(search_txt, case=False, na=False) |
                display_cards["device_asset"].str.contains(search_txt, case=False, na=False) |
                display_cards["description"].str.contains(search_txt, case=False, na=False)
            ]

        st.markdown(f"**Βρέθηκαν {len(display_cards)} βλάβες. Πατήστε πάνω σε οποιαδήποτε κάρτα για προβολή & επεξεργασία:**")
        st.markdown("---")

        for idx, row in display_cards.iterrows():
            badge = "🔴 OPEN" if row['status'] == "Open" else ("🟡 PENDING" if row['status'] == "Pending" else "🟢 CLOSED")
            card_title = f"{badge} | {row['ticket_id']} — {row['building_area']} ({row['category']})"
            
            with st.expander(card_title, expanded=False):
                col_info, col_edit = st.columns([1, 1], gap="medium")
                
                # ΑΡΙΣΤΕΡΗ ΣΤΗΛΗ: Πληροφορίες & Φωτογραφία
                with col_info:
                    st.markdown("##### 📌 Στοιχεία Βλάβης")
                    st.write(f"**Κωδικός:** `{row['ticket_id']}`")
                    st.write(f"**Περιοχή / Κτίριο:** {row['building_area']}")
                    st.write(f"**Συσκευή:** {row['device_asset']}")
                    st.write(f"**Προτεραιότητα:** {row['priority']}")
                    st.write(f"**Καταγεγραμμένες Ώρες:** {row.get('resolution_time_hrs', 0.0)} hrs")
                    st.write(f"**Υλικά που Χρησιμοποιήθηκαν:** {row.get('materials_used', 'N/A')}")
                    st.markdown(f"**Ιστορικό / Περιγραφή:**\n```text\n{row['description']}\n```")
                    
                    # Προβολή Φωτογραφίας
                    photo_val = row.get('photo_url', None)
                    if photo_val and str(photo_val).strip():
                        st.markdown("##### 📸 Φωτογραφία Βλάβης")
                        try:
                            st.image(photo_val, use_column_width=True)
                            if str(photo_val).startswith("http"):
                                st.markdown(f"[🔗 Άνοιγμα Εικόνας σε Νέο Παράθυρο / Download]({photo_val})")
                        except Exception:
                            st.warning("⚠️ Δεν ήταν δυνατή η φόρτωση της προεπισκόπησης της εικόνας.")
                    else:
                        st.info("ℹ️ Δεν υπάρχει καταχωρημένη φωτογραφία.")

                # ΔΕΞΙΑ ΣΤΗΛΗ: Φόρμα Άμεσης Ενημέρωσης
                with col_edit:
                    st.markdown("##### 🔄 Ενημέρωση & Κλείσιμο")
                    with st.form(key=f"form_update_{row['ticket_id']}"):
                        tech_name = st.text_input("👤 Τεχνικός / Χειριστής", placeholder="Ονοματεπώνυμο", key=f"tech_{row['ticket_id']}")
                        
                        st_options = ["Open", "Pending", "Closed"]
                        curr_st_idx = st_options.index(row['status']) if row['status'] in st_options else 0
                        up_status = st.selectbox("Κατάσταση", st_options, index=curr_st_idx, key=f"st_{row['ticket_id']}")
                        
                        up_hours = st.number_input("⏱️ Σύνολο Ωρών (hrs)", min_value=0.0, max_value=200.0, value=float(row.get('resolution_time_hrs', 0.0) or 0.0), step=0.5, key=f"hrs_{row['ticket_id']}")
                        
                        up_mats = st.text_area("🛠️ Υλικά / Ανταλλακτικά", value=str(row.get('materials_used', '') or ''), key=f"mat_{row['ticket_id']}")
                        
                        new_notes = st.text_area("✍️ Νέες Ενέργειες", placeholder="Γράψτε τι διορθώθηκε...", key=f"notes_{row['ticket_id']}")
                        
                        up_file = st.file_uploader("📸 Προσθήκη / Αλλαγή Φωτογραφίας", type=["jpg", "jpeg", "png"], key=f"img_{row['ticket_id']}")

                        if st.form_submit_button("💾 Αποθήκευση Αλλαγών"):
                            now_str = datetime.now().strftime('%d/%m %H:%M')
                            t_prefix = f" [Τεχνικός: {tech_name}]" if tech_name.strip() else ""
                            
                            updated_desc = row['description']
                            if new_notes.strip():
                                updated_desc += f"\n[{now_str}{t_prefix}]: {new_notes.strip()}"
                            elif tech_name.strip():
                                updated_desc += f"\n[{now_str}{t_prefix}]: Αλλαγή κατάστασης σε {up_status}."

                            payload = {
                                "status": up_status,
                                "resolution_time_hrs": float(up_hours),
                                "materials_used": up_mats,
                                "description": updated_desc
                            }
                            
                            if up_file:
                                new_photo_data = save_photo(up_file, row['ticket_id'])
                                if new_photo_data:
                                    payload["photo_url"] = new_photo_data

                            supabase.table("tickets").update(payload).eq("ticket_id", row['ticket_id']).execute()
                            st.success(f"✅ Η βλάβη {row['ticket_id']} ενημερώθηκε!")
                            st.rerun()
    else:
        st.info("Δεν βρέθηκαν καταχωρημένες βλάβες.")

# TAB 3: FULL HISTORY & EXPORT
with tab3:
    st.subheader("📊 Πλήρης Πίνακας & Εξαγωγή Δεδομένων")
    if not df_tickets.empty:
        st.dataframe(df_tickets, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχει διαθέσιμο ιστορικό.")
