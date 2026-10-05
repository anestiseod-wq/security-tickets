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
# 2. MODERN HIGH-CONTRAST THEME (CSS)
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

    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 16px; 
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 1.6rem; }

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

    div[data-testid="stForm"] { 
        background-color: #1e293b; 
        border: 1px solid #334155; 
        padding: 22px; 
        border-radius: 14px; 
    }
    </style>
""", unsafe_allow_html=True)

# Helper: Μετατροπή Εικόνας Κάμερας/Αρχείου σε Base64
def process_image(img_file):
    if img_file is not None:
        try:
            bytes_data = img_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode()
            mime_type = getattr(img_file, 'type', 'image/jpeg') or 'image/jpeg'
            return f"data:{mime_type};base64,{b64_str}"
        except Exception:
            return None
    return None

# ---------------------------------------------------------
# 3. DATA RETRIEVAL & METRICS CALCULATIONS
# ---------------------------------------------------------
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

# Υπολογισμοί Συνόλων & KPIs
HOURLY_RATE = 25.0  # Εκτιμώμενο κόστος εργασίας τεχνικού ανά ώρα (€/h)

total_tck = len(df_tickets)
open_tck = len(df_tickets[df_tickets["status"] == "Open"]) if not df_tickets.empty else 0
pending_tck = len(df_tickets[df_tickets["status"] == "Pending"]) if not df_tickets.empty else 0
closed_tck = len(df_tickets[df_tickets["status"] == "Closed"]) if not df_tickets.empty else 0

total_hours = 0.0
total_labor_cost = 0.0
avg_days_to_close = 0.0

if not df_tickets.empty:
    if "resolution_time_hrs" in df_tickets.columns:
        df_tickets["resolution_time_hrs"] = pd.to_numeric(df_tickets["resolution_time_hrs"], errors="coerce").fillna(0.0)
        total_hours = float(df_tickets["resolution_time_hrs"].sum())
        total_labor_cost = total_hours * HOURLY_RATE

    # Υπολογισμός Ημερών Αποκατάστασης (MTTR)
    if "created_at" in df_tickets.columns:
        df_tickets["created_dt"] = pd.to_datetime(df_tickets["created_at"], errors="coerce")
        df_tickets["updated_dt"] = pd.to_datetime(df_tickets.get("updated_at", df_tickets["created_at"]), errors="coerce")
        
        closed_df = df_tickets[df_tickets["status"] == "Closed"].copy()
        if not closed_df.empty:
            closed_df["duration_days"] = (closed_df["updated_dt"] - closed_df["created_dt"]).dt.total_seconds() / 86400.0
            avg_days_to_close = float(closed_df["duration_days"].mean())

# ---------------------------------------------------------
# 4. HEADER & DASHBOARD METRICS
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Papastratos (PMI) - Security Systems & Maintenance
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 600;">
                    Διαχειριστικό Πάνελ Βλαβών, Υπολογισμός Κόστους, Ωρών, Κάμερας & Ιστορικού
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.8); padding: 8px 16px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800;">● SYSTEM OPERATIONAL</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# KPIs Bar
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Σύνολο Βλαβών", total_tck)
k2.metric("🔴 Ανοιχτές", open_tck)
k3.metric("🟡 Εκκρεμείς", pending_tck)
k4.metric("🟢 Κλειστές", closed_tck)
k5.metric("⏱️ Σύνολο Ωρών", f"{total_hours:.1f}h")
k6.metric("📅 Μ.Ο. Ημερών", f"{avg_days_to_close:.1f} μέρες")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 1. Καταχώρηση Νέας Βλάβης (με Κάμερα)", "📋 2. Διαχείριση, Κάρτες & Ιστορικό", "📊 3. Αναλυτικά Σύνολα, Κόστη & KPIs"])

# TAB 1: NEW TICKET WITH CAMERA
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

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή της βλάβης...")
        
        st.markdown("##### 📸 Λήψη Φωτογραφίας (Κάμερα Κινητού/PC) ή Μεταφόρτωση Αρχείου")
        cam_col, file_col = st.columns(2)
        with cam_col:
            cam_photo = st.camera_input("📷 Λήψη από Κάμερα")
        with file_col:
            upload_photo = st.file_uploader("📁 Επιλογή Αρχείου Εικόνας", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("➕ Καταχώρηση Νέας Βλάβης στη Βάση"):
            active_photo = cam_photo if cam_photo is not None else upload_photo
            photo_b64 = process_image(active_photo)
            
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
            if photo_b64:
                insert_payload["photo_url"] = photo_b64
                
            supabase.table("tickets").insert(insert_payload).execute()
            st.success(f"✅ Η βλάβη **{tck_id}** καταχωρήθηκε επιτυχώς!")
            st.rerun()

# TAB 2: INTERACTIVE CARDS & AUDIT HISTORY
with tab2:
    st.subheader("📋 Πίνακας Βλαβών & Ιστορικό Ενεργειών (Ανοιχτές & Κλειστές)")
    
    if not df_tickets.empty:
        c_filter, c_search = st.columns([1, 2])
        with c_filter:
            status_filter = st.selectbox("Φιλτράρισμα Κατάστασης:", ["Όλες οι Βλάβες", "🔴 Ανοιχτές (Open & Pending)", "🟢 Ολοκληρωμένες (Closed)"])
        with c_search:
            search_txt = st.text_input("🔍 Αναζήτηση σε όλες τις βλάβες:", placeholder="Αναζήτηση κωδικού, περιοχής, τεχνικού, υλικών...")

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

        st.markdown(f"**Βρέθηκαν {len(display_cards)} βλάβες:**")
        st.markdown("---")

        for idx, row in display_cards.iterrows():
            badge = "🔴 OPEN" if row['status'] == "Open" else ("🟡 PENDING" if row['status'] == "Pending" else "🟢 CLOSED")
            card_title = f"{badge} | {row['ticket_id']} — {row['building_area']} ({row['category']})"
            
            with st.expander(card_title, expanded=False):
                col_info, col_edit = st.columns([1, 1], gap="medium")
                
                with col_info:
                    st.markdown("##### 📌 Στοιχεία & Ιστορικό Κινήσεων")
                    st.write(f"**Κωδικός:** `{row['ticket_id']}`")
                    st.write(f"**Περιοχή / Κτίριο:** {row['building_area']}")
                    st.write(f"**Συσκευή:** {row['device_asset']}")
                    st.write(f"**Προτεραιότητα:** {row['priority']}")
                    st.write(f"**Ώρες Αποκατάστασης:** {row.get('resolution_time_hrs', 0.0)} hrs")
                    st.write(f"**Υλικά που Χρησιμοποιήθηκαν:** {row.get('materials_used', 'N/A')}")
                    
                    st.markdown("**📜 Πλήρες Ιστορικό Ενεργειών:**")
                    st.text_area("Audit Trail", value=str(row['description']), height=150, disabled=True, key=f"hist_{row['ticket_id']}")
                    
                    # Φωτογραφία
                    photo_val = row.get('photo_url', None)
                    if photo_val and str(photo_val).strip():
                        st.markdown("##### 📸 Φωτογραφία Βλάβης")
                        try:
                            st.image(photo_val, use_column_width=True)
                        except Exception:
                            st.warning("⚠️ Δεν ήταν δυνατή η φόρτωση της προεπισκόπησης της φωτογραφίας.")
                    else:
                        st.info("ℹ️ Δεν έχει καταχωρηθεί φωτογραφία.")

                with col_edit:
                    st.markdown("##### 🔄 Ενημέρωση Βλάβης & Νέα Φωτογραφία")
                    with st.form(key=f"form_update_{row['ticket_id']}"):
                        tech_name = st.text_input("👤 Τεχνικός / Χειριστής", placeholder="Ονοματεπώνυμο", key=f"tech_{row['ticket_id']}")
                        
                        st_options = ["Open", "Pending", "Closed"]
                        curr_st_idx = st_options.index(row['status']) if row['status'] in st_options else 0
                        up_status = st.selectbox("Κατάσταση", st_options, index=curr_st_idx, key=f"st_{row['ticket_id']}")
                        
                        up_hours = st.number_input("⏱️ Σύνολο Ωρών (hrs)", min_value=0.0, max_value=200.0, value=float(row.get('resolution_time_hrs', 0.0) or 0.0), step=0.5, key=f"hrs_{row['ticket_id']}")
                        
                        up_mats = st.text_area("🛠️ Υλικά / Ανταλλακτικά", value=str(row.get('materials_used', '') or ''), key=f"mat_{row['ticket_id']}")
                        
                        new_notes = st.text_area("✍️ Προσθήκη Νέων Ενεργειών", placeholder="Γράψτε τι διορθώθηκε...", key=f"notes_{row['ticket_id']}")
                        
                        st.markdown("##### 📸 Νέα Λήψη από Κάμερα ή Αρχείο")
                        u_cam = st.camera_input("📷 Λήψη Φωτογραφίας", key=f"cam_{row['ticket_id']}")
                        u_file = st.file_uploader("📁 Μεταφόρτωση Αρχείου", type=["jpg", "jpeg", "png"], key=f"img_{row['ticket_id']}")

                        if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης"):
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
                                "description": updated_desc,
                                "updated_at": datetime.now().isoformat()
                            }
                            
                            active_up = u_cam if u_cam is not None else u_file
                            if active_up is not None:
                                new_b64 = process_image(active_up)
                                if new_b64:
                                    payload["photo_url"] = new_b64

                            supabase.table("tickets").update(payload).eq("ticket_id", row['ticket_id']).execute()
                            st.success(f"✅ Η βλάβη {row['ticket_id']} ενημερώθηκε επιτυχώς!")
                            st.rerun()
    else:
        st.info("Δεν βρέθηκαν καταχωρημένες βλάβες.")

# TAB 3: FULL ANALYTICS & TOTAL COSTS
with tab3:
    st.subheader("📊 Αναλυτικά Σύνολα, Κόστη Εργασίας & KPIs")
    if not df_tickets.empty:
        c_cost1, c_cost2, c_cost3 = st.columns(3)
        c_cost1.metric("⏱️ Συνολικές Ώρες Εργασίας", f"{total_hours:.1f} hrs")
        c_cost2.metric("💰 Εκτιμώμενο Κόστος Εργασίας (€25/h)", f"€{total_labor_cost:,.2f}")
        c_cost3.metric("📅 Μέσος Χρόνος Αποκατάστασης", f"{avg_days_to_close:.1f} ημέρες")
        
        st.markdown("---")
        st.markdown("##### 📋 Πλήρης Πίνακας Ιστορικού Βλαβών")
        st.dataframe(df_tickets, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχει διαθέσιμο ιστορικό.")
