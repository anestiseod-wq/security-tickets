import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE CONNECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="PMI Miscellaneous Issues",
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
# 2. MODERN HIGH-CONTRAST SOC THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; font-family: 'Inter', system-ui, sans-serif; }
    
    .pmi-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 50%, rgba(2, 132, 199, 0.8) 100%);
        backdrop-filter: blur(12px);
        padding: 22px 28px;
        border-radius: 18px;
        border: 1px solid rgba(56, 189, 248, 0.4);
        margin-bottom: 25px;
        box-shadow: 0 10px 30px -5px rgba(2, 132, 199, 0.3);
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        font-size: 0.98rem !important;
    }
    
    label { color: #cbd5e1 !important; font-weight: 600 !important; font-size: 0.92rem !important; }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff !important;
        border: 1px solid #38bdf8;
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 16px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #0c4a6e 100%);
        border-color: #7dd3fc;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5);
    }

    .ticket-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    .ticket-card:hover { border-color: #38bdf8; }

    .history-card {
        background: #1e293b;
        border-left: 5px solid #38bdf8;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    div[data-testid="stForm"] { background-color: #0f172a; border: 1px solid #334155; padding: 22px; border-radius: 16px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS & SAFE DATA PREPARATION
# ---------------------------------------------------------
def generate_ticket_id():
    try:
        res = supabase.table("tickets").select("id").order("id", desc=True).limit(1).execute()
        next_num = (res.data[0]['id'] + 1) if res.data else 1
    except Exception:
        next_num = 1
    return f"TCK-{next_num:04d}"

def upload_photos_to_supabase(files, ticket_id, photo_type="BEFORE"):
    urls = []
    for idx, file in enumerate(files):
        if file is not None:
            file_ext = file.name.split('.')[-1] if hasattr(file, 'name') and file.name else 'jpg'
            file_path = f"{ticket_id}/{photo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}.{file_ext}"
            file_bytes = file.getvalue()
            supabase.storage.from_("ticket-photos").upload(
                file_path, file_bytes, file_options={"content-type": f"image/{file_ext}"}
            )
            public_url = supabase.storage.from_("ticket-photos").get_public_url(file_path)
            supabase.table("ticket_photos").insert({
                "ticket_id": ticket_id,
                "photo_url": public_url,
                "photo_type": photo_type
            }).execute()
            urls.append(public_url)
    return urls

# Ανάκτηση και ασφαλής προετοιμασία DataFrame
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

# Ασφαλής εξασφάλιση στηλών για αποφυγή KeyError
for col in ["materials_used", "resolution_time_hrs", "closed_at"]:
    if not df_tickets.empty and col not in df_tickets.columns:
        df_tickets[col] = 0.0 if col == "resolution_time_hrs" else "N/A"

# Session State για επιλογή Ticket
if "active_ticket_id" not in st.session_state:
    st.session_state["active_ticket_id"] = None

# ---------------------------------------------------------
# 4. PMI HEADER & MAIN KPI METRICS
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ PMI Miscellaneous Issues
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 500;">
                    Security Systems & Site Maintenance Operations (Aspropyrgos Facility)
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.7); padding: 8px 16px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800; font-size: 0.9rem;">● LIVE SUPABASE DATABASE</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Υπολογισμοί KPIs
total_tck = len(df_tickets)
open_tck = len(df_tickets[df_tickets["status"].isin(["Open", "In Progress", "Pending"])]) if not df_tickets.empty else 0
closed_df = df_tickets[df_tickets["status"] == "Closed"] if not df_tickets.empty else pd.DataFrame()
closed_count = len(closed_df)

# MTTR & Συνολικές Ώρες
if not closed_df.empty and "resolution_time_hrs" in closed_df.columns:
    closed_df["resolution_time_hrs"] = pd.to_numeric(closed_df["resolution_time_hrs"], errors='coerce').fillna(0)
    total_hours = closed_df["resolution_time_hrs"].sum()
    mttr = closed_df["resolution_time_hrs"].mean()
else:
    total_hours = 0.0
    mttr = 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Συνολικά Tickets", total_tck)
col2.metric("Ανοιχτά / Σε εξέλιξη", open_tck)
col3.metric("Ολοκληρωμένα (Closed)", closed_count)
col4.metric("Μ.Ο. Επισκευής (MTTR)", f"{mttr:.1f} hrs", delta=f"Σύνολο: {total_hours:.1f} hrs")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 Νέο Ticket Βλάβης", "📊 Ανοιχτές Βλάβες & Πίνακας", "🔍 Αναλυτική Καρτέλα & Ιστορικό"])

# TAB 1: ΝΕΟ TICKET
with tab1:
    st.subheader("Καταγραφή Νέου Περιστατικού")
    with st.form("new_ticket_form", clear_on_submit=True):
        st.markdown("##### 👤 Στοιχεία Συντάκτη / Υπογραφή")
        cs1, cs2 = st.columns(2)
        with cs1:
            author_role = st.selectbox("Ρόλος Συντάκτη", ["Τεχνικός Ασφαλείας / Security Tech", "IT Support / Network Expert", "Supervisor / Team Lead", "Site Security / SOC Operator", "Εξωτερικός Εργολάβος / Vendor"])
        with cs2:
            author_name = st.text_input("Ονοματεπώνυμο Χειριστή", placeholder="π.χ. Ανέστης Θεοδωρίδης")

        st.markdown("---")
        st.markdown("##### 🛠️ Στοιχεία Βλάβης & Περιοχή")
        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox("Κατηγορία Συστήματος", ["CCTV", "ACS (Access Control)", "Fire Alarm", "Intrusion Alarm", "Gates/Barriers", "Network/PoE", "Infrastructure/Facility"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Κεντρική Είσοδος")
            floor_level = st.selectbox("Όροφος / Επίπεδο", ["Υπόγειο -2", "Υπόγειο -1", "Ισόγειο / Ground", "1ος Όροφος", "2ος Όροφος", "3ος Όροφος", "Roof / Ταράτσα", "Εξωτερικός Χώρος"])
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. CAM-12 / Reader-04")
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
        with c2:
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "In Progress", "Pending"])
            materials = st.text_input("Αρχικά Υλικά / Ανταλλακτικά")
            description = st.text_area("Περιγραφή Βλάβης")

        st.markdown("##### 📸 Φωτογραφίες Βλάβης (Before)")
        up_files = st.file_uploader("Επιλογή από Gallery/Αρχεία (Πολλαπλά)", type=["jpg", "png", "heic"], accept_multiple_files=True)
        cam_file = st.camera_input("Ή Λήψη από Κάμερα Κινητού")

        if st.form_submit_button("💾 Δημιουργία Ticket"):
            t_id = generate_ticket_id()
            full_author = f"{author_name} ({author_role})" if author_name else author_role
            
            new_ticket = {
                "ticket_id": t_id,
                "category": category,
                "building_area": f"{building_area} [{floor_level}]",
                "device_asset": device_asset,
                "priority": priority,
                "status": status,
                "description": f"[{full_author}]: {description}",
                "materials_used": materials,
                "resolution_time_hrs": 0.0
            }
            supabase.table("tickets").insert(new_ticket).execute()

            all_files = (up_files if up_files else []) + ([cam_file] if cam_file else [])
            if all_files:
                upload_photos_to_supabase(all_files, t_id, photo_type="BEFORE")

            supabase.table("ticket_updates").insert({
                "ticket_id": t_id,
                "status_changed_to": status,
                "comment": f"Αρχική καταγραφή βλάβης από {full_author}.",
                "action_type": "CREATED"
            }).execute()

            st.success(f"✅ Το Ticket **{t_id}** δημιουργήθηκε επιτυχώς με υπογραφή {full_author}!")
            st.rerun()

# TAB 2: ΠΙΝΑΚΑΣ & ΔΙΑΔΡΑΣΤΙΚΕΣ ΚΑΡΤΕΣ
with tab2:
    st.subheader("📋 Ανοιχτές Βλάβες & Διαχείριση")
    if not df_tickets.empty:
        open_tickets_df = df_tickets[df_tickets["status"].isin(["Open", "In Progress", "Pending"])]
        
        if not open_tickets_df.empty:
            st.markdown("##### ⚡ Κάντε κλικ σε μια βλάβη για άμεση προβολή & ενημέρωση:")
            cols = st.columns(2)
            for idx, (_, row) in enumerate(open_tickets_df.iterrows()):
                col = cols[idx % 2]
                with col:
                    st.markdown(f"""
                    <div class="ticket-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#38bdf8;">📌 {row['ticket_id']} - {row['category']}</h4>
                            <span style="background:#ef4444; color:white; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem;">{row['priority']}</span>
                        </div>
                        <p style="margin:6px 0; color:#cbd5e1;"><b>Περιοχή:</b> {row['building_area']} | <b>Asset:</b> {row['device_asset']}</p>
                        <p style="margin:0; color:#94a3b8; font-size:0.9rem;">Status: <b style="color:#f59e0b;">{row['status']}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🔍 Προβολή & Διαχείριση {row['ticket_id']}", key=f"btn_{row['ticket_id']}"):
                        st.session_state["active_ticket_id"] = row['ticket_id']
                        st.rerun()
        else:
            st.success("🎉 Δεν υπάρχουν ανοιχτές βλάβες σε εκκρεμότητα!")

        st.markdown("---")
        st.markdown("##### 📊 Πλήρης Πίνακας Όλων των Βλαβών (Αρχείο)")
        
        # Download αρχείου Excel/CSV
        csv_data = df_tickets.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Εξαγωγή Αναφοράς Βλαβών (CSV / Excel)",
            data=csv_data,
            file_name=f"PMI_Tickets_Report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.dataframe(df_tickets[["ticket_id", "created_at", "category", "building_area", "device_asset", "priority", "status", "materials_used", "resolution_time_hrs"]], use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένα tickets στη βάση.")

# TAB 3: ΑΝΑΛΥΤΙΚΗ ΚΑΡΤΕΛΑ & UPDATE
with tab3:
    st.subheader("🔍 Αναλυτική Διαχείριση Ticket & Ιστορικό")
    if not df_tickets.empty:
        ticket_options = df_tickets["ticket_id"].tolist()
        
        # Προεπιλογή αν πατήθηκε κουμπί από το Tab 2
        default_index = 0
        if st.session_state["active_ticket_id"] in ticket_options:
            default_index = ticket_options.index(st.session_state["active_ticket_id"])
            
        selected_tck_id = st.selectbox("Επιλέξτε Ticket ID για προβολή/ενημέρωση:", options=ticket_options, index=default_index)
        
        t_data = supabase.table("tickets").select("*").eq("ticket_id", selected_tck_id).single().execute().data
        p_data = supabase.table("ticket_photos").select("*").eq("ticket_id", selected_tck_id).execute().data
        u_data = supabase.table("ticket_updates").select("*").eq("ticket_id", selected_tck_id).order("created_at", desc=True).execute().data

        col_info, col_photos = st.columns([1, 1])
        
        with col_info:
            st.markdown(f"### 📌 {t_data['ticket_id']} - {t_data['category']}")
            st.write(f"**Περιοχή / Όροφος:** {t_data['building_area']}")
            st.write(f"**Συσκευή:** {t_data['device_asset']}")
            st.write(f"**Προτεραιότητα:** `{t_data['priority']}` | **Κατάσταση:** `{t_data['status']}`")
            st.write(f"**Περιγραφή:** {t_data['description']}")
            st.write(f"**Υλικά:** {t_data.get('materials_used', 'N/A')}")
            st.write(f"**Ώρες Αποκατάστασης:** `{t_data.get('resolution_time_hrs', 0.0)} hrs`")
            st.caption(f"Ημερομηνία Δημιουργίας: {t_data['created_at']}")

        with col_photos:
            st.markdown("### 📸 Φωτογραφικό Υλικό")
            if p_data:
                tab_before, tab_after = st.tabs(["📷 Βλάβη (Before)", "🛠️ Αποκατάσταση (After)"])
                with tab_before:
                    bef_photos = [p['photo_url'] for p in p_data if p.get('photo_type') == 'BEFORE']
                    if bef_photos:
                        st.image(bef_photos, width=220, caption=["Before"]*len(bef_photos))
                    else:
                        st.write("Καμία φωτογραφία βλάβης.")
                with tab_after:
                    aft_photos = [p['photo_url'] for p in p_data if p.get('photo_type') == 'AFTER']
                    if aft_photos:
                        st.image(aft_photos, width=220, caption=["After"]*len(aft_photos))
                    else:
                        st.write("Καμία φωτογραφία αποκατάστασης.")
            else:
                st.write("Δεν υπάρχουν συνημμένες φωτογραφίες.")

        st.markdown("---")
        
        st.markdown("### 🔄 Προσθήκη Ενημέρωσης & Υπογραφή Τεχνικού")
        with st.form("update_ticket_form"):
            cu_prof1, cu_prof2 = st.columns(2)
            with cu_prof1:
                updater_role = st.selectbox("Ρόλος Χρήστη που Ενημερώνει", ["Τεχνικός Ασφαλείας / Security Tech", "IT Support / Network Expert", "Supervisor / Team Lead", "Site Security / SOC Operator", "Εξωτερικός Εργολάβος / Vendor"])
            with cu_prof2:
                updater_name = st.text_input("Ονοματεπώνυμο Χρήστη", placeholder="π.χ. Ανέστης Θεοδωρίδης")

            cu1, cu2 = st.columns(2)
            with cu1:
                new_status = st.selectbox("Νέα Κατάσταση:", ["Open", "In Progress", "Pending", "Resolved", "Closed"], index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(t_data['status']))
                add_materials = st.text_input("Επιπλέον Υλικά / Ανταλλακτικά:")
                res_time = st.number_input("Ώρες Εργασίας / Αποκατάστασης:", min_value=0.0, value=float(t_data.get('resolution_time_hrs', 0.0) or 0.0), step=0.5)
            with cu2:
                comment = st.text_area("Σχόλιο / Πρόοδος Εργασιών:")
                new_photos = st.file_uploader("Προσθήκη Φωτογραφιών Αποκατάστασης (After):", type=["jpg", "png", "heic"], accept_multiple_files=True)

            if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης"):
                updater_full = f"{updater_name} ({updater_role})" if updater_name else updater_role
                
                upd_payload = {
                    "status": new_status,
                    "resolution_time_hrs": res_time,
                    "materials_used": f"{t_data.get('materials_used', '')} | {add_materials}" if add_materials else t_data.get('materials_used', '')
                }
                if new_status == "Closed":
                    upd_payload["closed_at"] = datetime.now().isoformat()
                
                supabase.table("tickets").update(upd_payload).eq("ticket_id", selected_tck_id).execute()

                if new_photos:
                    upload_photos_to_supabase(new_photos, selected_tck_id, photo_type="AFTER")

                supabase.table("ticket_updates").insert({
                    "ticket_id": selected_tck_id,
                    "status_changed_to": new_status,
                    "comment": f"[{updater_full}]: {comment if comment else 'Ενημέρωση στοιχείων.'}",
                    "action_type": "UPDATE"
                }).execute()

                st.success(f"✅ Το Ticket ενημερώθηκε επιτυχώς από τον/την {updater_full}!")
                st.rerun()

        st.markdown("### 📜 Ιστορικό Ενεργειών (Audit Trail)")
        if u_data:
            for log in u_data:
                st.markdown(f"""
                <div class="history-card">
                    <small style="color:#38bdf8;"><b>{log['created_at']}</b> — Status: <span style="color:#10b981;"><b>{log['status_changed_to']}</b></span></small><br>
                    <span style="color:#f1f5f9; font-size:1.02rem;">{log['comment']}</span>
                </div>
                """, unsafe_allow_html=True)
