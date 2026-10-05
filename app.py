import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE CONNECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="PMI - Security & Maintenance Tickets",
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
# 2. HIGH-CONTRAST MODERN THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { 
        background-color: #0f172a; 
        color: #f8fafc; 
        font-family: 'Inter', system-ui, -apple-system, sans-serif; 
    }
    
    .pmi-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #0284c7 100%);
        padding: 24px 30px;
        border-radius: 16px;
        border: 1px solid #38bdf8;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1.5px solid #475569 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    
    label { 
        color: #e2e8f0 !important; 
        font-weight: 700 !important; 
        font-size: 0.95rem !important;
        margin-bottom: 6px !important;
    }

    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 18px; 
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; font-size: 0.9rem; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 1.8rem; }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 12px 20px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #075985 100%) !important;
        border-color: #7dd3fc !important;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.4);
    }

    div[data-testid="stForm"] { 
        background-color: #1e293b; 
        border: 1px solid #334155; 
        padding: 24px; 
        border-radius: 16px; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    .ticket-detail-card {
        background-color: #1e293b;
        border-left: 5px solid #38bdf8;
        padding: 20px;
        border-radius: 14px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function για Upload Φωτογραφίας
def upload_pmi_photo(file, ticket_id):
    if file is not None:
        try:
            file_ext = file.name.split('.')[-1] if hasattr(file, 'name') and file.name else 'jpg'
            file_path = f"{ticket_id}/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            file_bytes = file.getvalue()
            
            supabase.storage.from_("ticket-photos").upload(
                file_path, file_bytes, file_options={"content-type": f"image/{file_ext}"}
            )
            public_url = supabase.storage.from_("ticket-photos").get_public_url(file_path)
            return public_url
        except Exception:
            return None
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
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.2rem; color: #ffffff !important; font-weight: 800; letter-spacing: -0.5px;">
                    🛡️ Papastratos (PMI) - Security Systems & Maintenance
                </h1>
                <p style="margin:6px 0 0 0; color: #38bdf8; font-size: 1.05rem; font-weight: 600;">
                    Διαχείριση Βλαβών, Καταγραφή Τεχνικών, Υλικών, Ώρες & Φωτογραφίες
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.8); padding: 10px 18px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800; font-size: 0.95rem;">● SYSTEM ONLINE</span>
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
k1.metric("Σύνολο Βλαβών", total_tck)
k2.metric("🔴 Ανοιχτές (Open)", open_tck)
k3.metric("🟡 Σε Εκκρεμότητα", pending_tck)
k4.metric("🟢 Ολοκληρωμένες", closed_tck)
k5.metric("⏱️ Σύνολο Ωρών", f"{total_hours:.1f} hrs")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS (1ο Tab: Καταχώρηση Νέας Βλάβης)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 1. Καταχώρηση Νέας Βλάβης", "📋 2. Διαχείριση, Ενημέρωση & Φωτογραφίες", "📊 3. Αναλυτικό Ιστορικό & Υλικά"])

# TAB 1: NEW TICKET FORM
with tab1:
    st.subheader("📝 Νέα Αναφορά Βλάβης / Συντήρησης")
    
    with st.form("new_ticket_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tck_id = st.text_input("Κωδικός Ticket", value=f"TCK-{datetime.now().strftime('%m%d-%H%M')}")
            creator_tech = st.text_input("👤 Τεχνικός / Χειριστής που Καταχωρεί τη Βλάβη", placeholder="π.χ. Ανέστης Θεοδωρίδης")
            category = st.selectbox("Κατηγορία Συστήματος", ["CCTV (Κάμερες)", "ACS (Access Control / Τουρνικέ)", "Fire Alarm (Πυρανίχνευση)", "Network / PoE / Fiber", "Άλλο"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Είσοδος Τουρνικέ DR_116")
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. Cam 20 / Reader CR.08L0.01.01")

        with f2:
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "Pending", "Closed"])
            duration_hrs = st.number_input("⏱️ Αρχικές Ώρες Εργασίας (hrs)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
            materials = st.text_area("🛠️ Υλικά / Ανταλλακτικά που Χρησιμοποιήθηκαν", placeholder="π.χ. 1x PoE Injector, 10m καλώδιο UTP Cat6, 2x RJ45")

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή της βλάβης...")
        
        st.markdown("##### 📸 Φωτογραφία Βλάβης (Προαιρετικό)")
        img_file = st.file_uploader("Μεταφόρτωση Εικόνας / Snapshot", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("➕ Καταχώρηση Νέας Βλάβης στη Βάση"):
            photo_url = upload_pmi_photo(img_file, tck_id) if img_file else None
            creator_prefix = f"[Καταχώρηση: {creator_tech}]\n" if creator_tech.strip() else ""
            full_initial_desc = f"{creator_prefix}{description}"
            
            insert_payload = {
                "ticket_id": tck_id,
                "category": category,
                "building_area": building_area,
                "device_asset": device_asset,
                "priority": priority,
                "status": status,
                "description": full_initial_desc,
                "materials_used": materials if materials else "Καμία χρήση υλικών",
                "resolution_time_hrs": float(duration_hrs)
            }
            if photo_url:
                insert_payload["photo_url"] = photo_url
                
            supabase.table("tickets").insert(insert_payload).execute()
            st.success(f"✅ Η βλάβη **{tck_id}** καταχωρήθηκε επιτυχώς!")
            st.rerun()

# TAB 2: UPDATE & INSPECT TICKETS (Side-by-Side Layout)
with tab2:
    st.subheader("📋 Ενημέρωση, Επεξεργασία & Προβολή Φωτογραφίας")
    
    if not df_tickets.empty:
        filter_status = st.radio("Φίλτρο Προβολής Βλαβών:", ["Όλες οι Βλάβες", "Μόνο Ανοιχτές (Open & Pending)", "Μόνο Ολοκληρωμένες (Closed)"], horizontal=True)
        
        filtered_df = df_tickets.copy()
        if filter_status == "Μόνο Ανοιχτές (Open & Pending)":
            filtered_df = filtered_df[filtered_df["status"] != "Closed"]
        elif filter_status == "Μόνο Ολοκληρωμένες (Closed)":
            filtered_df = filtered_df[filtered_df["status"] == "Closed"]
            
        if not filtered_df.empty:
            ticket_options = [f"{row['ticket_id']} | {row['building_area']} | [{row['status']}]" for _, row in filtered_df.iterrows()]
            selected_option = st.selectbox("🎯 Επιλέξτε Βλάβη για Προβολή / Επεξεργασία:", options=ticket_options)
            
            selected_id = selected_option.split(" | ")[0]
            tck_data = filtered_df[filtered_df["ticket_id"] == selected_id].iloc[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ΔΙΑΤΑΞΗ 2 ΣΤΗΛΩΝ (Side-by-Side): Αριστερά Πληροφορίες/Φωτό - Δεξιά Φόρμα Ενημέρωσης
            col_left, col_right = st.columns([1, 1], gap="large")
            
            with col_left:
                st.markdown("##### 🔍 Στοιχεία Βλάβης & Φωτογραφία")
                status_color = "#ef4444" if tck_data['status'] == "Open" else ("#f59e0b" if tck_data['status'] == "Pending" else "#10b981")
                
                st.markdown(f"""
                <div class="ticket-detail-card" style="border-left-color: {status_color};">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                        <h3 style="margin:0; color:#38bdf8;">📌 {tck_data['ticket_id']} — {tck_data['category']}</h3>
                        <span style="background:{status_color}; color:#ffffff; padding:4px 12px; border-radius:6px; font-weight:800;">{tck_data['status']}</span>
                    </div>
                    <hr style="border-color:#334155; margin:12px 0;">
                    <p style="margin:4px 0; color:#f8fafc;"><b>📍 Περιοχή/Κτίριο:</b> {tck_data['building_area']}</p>
                    <p style="margin:4px 0; color:#f8fafc;"><b>🖥️ Συσκευή:</b> {tck_data['device_asset']}</p>
                    <p style="margin:4px 0; color:#f8fafc;"><b>🚨 Προτεραιότητα:</b> {tck_data['priority']}</p>
                    <p style="margin:4px 0; color:#f8fafc;"><b>⏱️ Καταγεγραμμένες Ώρες:</b> {tck_data.get('resolution_time_hrs', 0.0)} hrs</p>
                    <p style="margin:4px 0; color:#cbd5e1;"><b>🛠️ Υλικά/Ανταλλακτικά:</b> {tck_data.get('materials_used', 'N/A')}</p>
                    <p style="margin:10px 0 0 0; color:#cbd5e1;"><b>📝 Ιστορικό Ενεργειών:</b><br>{tck_data['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Εμφάνιση Φωτογραφίας αν υπάρχει
                photo_url = tck_data.get('photo_url', None)
                if photo_url and str(photo_url).startswith("http"):
                    st.markdown("###### 🖼️ Εικόνα / Snapshot Βλάβης")
                    st.image(photo_url, use_column_width=True, caption=f"Φωτογραφία {tck_data['ticket_id']}")
                else:
                    st.info("ℹ️ Δεν έχει μεταφορτωθεί φωτογραφία για αυτή τη βλάβη.")

            with col_right:
                st.markdown("##### 🔄 Φόρμα Ενημέρωσης & Αλλαγής Κατάστασης")
                with st.form("update_ticket_form", clear_on_submit=False):
                    u_tech = st.text_input("👤 Ονοματεπώνυμο Τεχνικού / Χειριστή", placeholder="π.χ. Ανέστης Θεοδωρίδης")
                    
                    status_list = ["Open", "Pending", "Closed"]
                    curr_idx = status_list.index(tck_data['status']) if tck_data['status'] in status_list else 0
                    new_status = st.selectbox("Νέα Κατάσταση Βλάβης", status_list, index=curr_idx)
                    
                    hours_val = float(tck_data.get('resolution_time_hrs', 0.0) or 0.0)
                    new_hours = st.number_input("⏱️ Σύνολο Ωρών Εργασίας (hrs)", min_value=0.0, max_value=200.0, value=hours_val, step=0.5)
                    
                    curr_mat = str(tck_data.get('materials_used', '') or '')
                    updated_materials = st.text_area("🛠️ Υλικά / Ανταλλακτικά που Χρησιμοποιήθηκαν", value=curr_mat, placeholder="π.χ. 1x PoE Injector, 10m UTP Cat6")
                    
                    add_notes = st.text_area("✍️ Νέες Ενέργειες / Σημειώσεις", placeholder="Γράψτε τις νέες ενέργειες που πραγματοποιήθηκαν...")
                    
                    st.markdown("##### 📸 Προσθήκη / Ενημέρωση Φωτογραφίας")
                    new_img_file = st.file_uploader("Νέα Εικόνα Επισκευής (After)", type=["jpg", "jpeg", "png"], key="update_img")

                    if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης & Ενημέρωση Βάσης"):
                        tech_str = f" [Τεχνικός: {u_tech}]" if u_tech.strip() else ""
                        updated_desc = tck_data['description']
                        
                        now_stamp = datetime.now().strftime('%d/%m %H:%M')
                        if add_notes.strip():
                            updated_desc += f"\n[{now_stamp}{tech_str}]: {add_notes.strip()}"
                        elif u_tech.strip():
                            updated_desc += f"\n[{now_stamp}{tech_str}]: Ενημέρωση κατάστασης σε {new_status}."
                        
                        update_payload = {
                            "status": new_status,
                            "resolution_time_hrs": float(new_hours),
                            "materials_used": updated_materials,
                            "description": updated_desc
                        }
                        
                        if new_img_file:
                            uploaded_url = upload_pmi_photo(new_img_file, selected_id)
                            if uploaded_url:
                                update_payload["photo_url"] = uploaded_url
                        
                        supabase.table("tickets").update(update_payload).eq("ticket_id", selected_id).execute()
                        
                        st.success(f"✅ Η βλάβη **{selected_id}** ενημερώθηκε επιτυχώς!")
                        st.rerun()
        else:
            st.info("Δεν βρέθηκαν βλάβες για το επιλεγμένο φίλτρο.")
    else:
        st.info("Δεν υπάρχουν καταχωρημένες βλάβες στη βάση.")

# TAB 3: FULL HISTORY
with tab3:
    st.subheader("📊 Αναλυτικό Ιστορικό Βλαβών & Εξαγωγή Δεδομένων")
    if not df_tickets.empty:
        col_search, col_cat = st.columns(2)
        with col_search:
            search_query = st.text_input("🔍 Αναζήτηση (Κωδικός, Περιοχή, Συσκευή, Τεχνικός):", "")
        with col_cat:
            cat_filter = st.selectbox("Φιλτράρισμα ανά Κατηγορία:", ["Όλες"] + df_tickets["category"].unique().tolist())
            
        display_df = df_tickets.copy()
        if search_query:
            display_df = display_df[
                display_df["ticket_id"].str.contains(search_query, case=False, na=False) |
                display_df["building_area"].str.contains(search_query, case=False, na=False) |
                display_df["device_asset"].str.contains(search_query, case=False, na=False) |
                display_df["description"].str.contains(search_query, case=False, na=False)
            ]
        if cat_filter != "Όλες":
            display_df = display_df[display_df["category"] == cat_filter]
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχει διαθέσιμο ιστορικό.")
