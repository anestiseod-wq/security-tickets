import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
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
        padding: 24px 30px;
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
        padding: 18px;
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
        padding: 12px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #0c4a6e 100%);
        border-color: #7dd3fc;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5);
    }

    .history-card {
        background: #1e293b;
        border-left: 5px solid #38bdf8;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    div[data-testid="stForm"] { background-color: #0f172a; border: 1px solid #334155; padding: 24px; border-radius: 16px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS
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

# ---------------------------------------------------------
# 4. PMI HEADER & KPI METRICS
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.2rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ PMI Miscellaneous Issues
                </h1>
                <p style="margin:6px 0 0 0; color: #38bdf8; font-size: 1.05rem; font-weight: 500;">
                    Security Systems, Infrastructure & Maintenance Operations (Aspropyrgos Facility)
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.7); padding: 10px 18px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800; font-size: 0.95rem;">● LIVE DATABASE CONNECTED</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Ανάκτηση δεδομένων
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

total_tck = len(df_tickets)
open_tck = len(df_tickets[df_tickets["status"].isin(["Open", "In Progress", "Pending"])]) if not df_tickets.empty else 0
critical_tck = len(df_tickets[(df_tickets["priority"] == "Critical") & (df_tickets["status"] != "Closed")]) if not df_tickets.empty else 0
total_material_cost = df_tickets["material_cost"].sum() if not df_tickets.empty and "material_cost" in df_tickets.columns else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Συνολικά Tickets", total_tck)
col2.metric("Ανοιχτά / Σε εξέλιξη", open_tck)
col3.metric("Critical Εκκρεμή", critical_tck, delta="⚠️ Απαιτείται Ενέργεια" if critical_tck > 0 else "✅ Ομαλό", delta_color="inverse")
col4.metric("Συνολικό Κόστος Υλικών", f"{total_material_cost:,.2f} €")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 Νέο Ticket & Χάρτης", "📊 Πίνακας & Φίλτρα", "🔍 Αναλυτική Καρτέλα & Κόστη"])

# TAB 1: ΝΕΟ TICKET
with tab1:
    st.subheader("Καταγραφή Νέου Περιστατικού & Σημείο στο Χάρτη")
    
    # Διαδραστικός Χάρτης Ασπροπύργου (Default Center: Papastratos Facility)
    st.markdown("##### 📍 Επιλέξτε Ακριβές Σημείο Βλάβης στο Χάρτη Εγκαταστάσεων (Aspropyrgos Site)")
    default_lat, default_lon = 38.0385, 23.5930
    
    m = folium.Map(location=[default_lat, default_lon], zoom_start=17, tiles="OpenStreetMap")
    folium.Marker(
        [default_lat, default_lon], 
        popup="Papastratos Main Facility", 
        tooltip="Κάντε κλικ οπουδήποτε για τοποθέτηση βλάβης",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)
    
    map_data = st_folium(m, height=320, width="100%")
    
    selected_lat = map_data["last_clicked"]["lat"] if map_data and map_data.get("last_clicked") else default_lat
    selected_lon = map_data["last_clicked"]["lng"] if map_data and map_data.get("last_clicked") else default_lon
    
    st.caption(f"📌 Επιλεγμένες Συντεταγμένες: Lat: `{selected_lat:.6f}`, Lon: `{selected_lon:.6f}`")

    with st.form("new_ticket_form", clear_on_submit=True):
        st.markdown("##### 👤 Στοιχεία Συντάκτη / Υπογραφή")
        cs1, cs2 = st.columns(2)
        with cs1:
            author_role = st.selectbox("Ρόλος Συντάκτη", ["Τεχνικός Ασφαλείας / Security Tech", "IT Support / Network Expert", "Supervisor / Team Lead", "Site Security / SOC Operator", "Εξωτερικός Εργολάβος / Vendor"])
        with cs2:
            author_name = st.text_input("Ονοματεπώνυμο Χειριστή", placeholder="π.χ. Ανέστης Θεοδωρίδης")

        st.markdown("---")
        st.markdown("##### 🛠️ Στοιχεία Βλάβης & Τοποθεσία")
        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox("Κατηγορία Συστήματος", ["CCTV", "ACS (Access Control)", "Fire Alarm", "Intrusion Alarm", "Gates/Barriers", "Network/PoE", "Infrastructure/Facility"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Κεντρική Είσοδος")
            floor_level = st.selectbox("Όροφος / Επίπεδο", ["Υπόγειο -2", "Υπόγειο -1", "Ισόγειο / Ground", "1ος Όροφος", "2ος Όροφος", "3ος Όροφος", "Roof / Ταράτσα", "Εξωτερικός Χώρος"])
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. CAM-12 / Reader-04")
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
        with c2:
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "In Progress", "Pending"])
            description = st.text_area("Περιγραφή Βλάβης")

        st.markdown("---")
        st.markdown("##### 📦 Υλικά, Κόστος & Πόροι")
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            materials_source = st.selectbox("Προέλευση Υλικού", ["Αποθήκη Site (In Stock)", "Απαιτείται Αγορά (Purchase Order)", "Εγγύηση / Vendor Warranty", "Δεν απαιτήθηκαν υλικά"])
            materials = st.text_input("Περιγραφή Υλικών / Ανταλλακτικών")
        with cp2:
            material_cost = st.number_input("Εκτιμώμενο / Πραγματικό Κόστος Υλικών (€)", min_value=0.0, step=10.0)
            tech_count = st.number_input("Αριθμός Τεχνικών που απαιτήθηκαν", min_value=1, value=1)
        with cp3:
            est_hours = st.number_input("Εκτιμώμενες Ώρες Εργασίας", min_value=0.5, step=0.5, value=1.0)

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
                "materials_used": f"[{materials_source}] {materials}",
                "material_cost": material_cost,
                "resolution_time_hrs": est_hours
            }
            supabase.table("tickets").insert(new_ticket).execute()

            all_files = (up_files if up_files else []) + ([cam_file] if cam_file else [])
            if all_files:
                upload_photos_to_supabase(all_files, t_id, photo_type="BEFORE")

            supabase.table("ticket_updates").insert({
                "ticket_id": t_id,
                "status_changed_to": status,
                "comment": f"Αρχική καταγραφή βλάβης από {full_author}. Σημείο στο χάρτη: ({selected_lat:.4f}, {selected_lon:.4f}). Προέλευση υλικών: {materials_source}.",
                "action_type": "CREATED"
            }).execute()

            st.success(f"✅ Το Ticket **{t_id}** δημιουργήθηκε επιτυχώς με υπογραφή {full_author}!")
            st.rerun()

# TAB 2: ΠΙΝΑΚΑΣ & ΦΙΛΤΡΑ
with tab2:
    st.subheader("Αναζήτηση & Ιστορικό Βλαβών")
    if not df_tickets.empty:
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            search_query = st.text_input("🔍 Αναζήτηση (ID, Περιοχή, Asset):")
        with c_f2:
            status_filter = st.multiselect("Φίλτρο Status:", options=["Open", "In Progress", "Pending", "Resolved", "Closed"], default=["Open", "In Progress", "Pending"])

        filtered_df = df_tickets.copy()
        if status_filter:
            filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]
        if search_query:
            filtered_df = filtered_df[
                filtered_df["ticket_id"].str.contains(search_query, case=False, na=False) |
                filtered_df["building_area"].str.contains(search_query, case=False, na=False) |
                filtered_df["device_asset"].str.contains(search_query, case=False, na=False)
            ]

        st.dataframe(
            filtered_df[["ticket_id", "created_at", "category", "building_area", "device_asset", "priority", "status", "materials_used", "material_cost"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Δεν υπάρχουν καταχωρημένα tickets στη βάση.")

# TAB 3: ΑΝΑΛΥΤΙΚΗ ΚΑΡΤΕΛΑ & UPDATE
with tab3:
    st.subheader("🔍 Αναλυτική Διαχείριση Ticket & Κοστολόγηση")
    if not df_tickets.empty:
        selected_tck_id = st.selectbox("Επιλέξτε Ticket ID για προβολή/ενημέρωση:", options=df_tickets["ticket_id"].tolist())
        
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
            st.write(f"**Υλικά:** {t_data['materials_used']}")
            st.write(f"**Κόστος Υλικών:** `{t_data.get('material_cost', 0.0):,.2f} €`")
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
                updater_name = st.text_input("Ονοματεπώνυμο Χρήστη", placeholder="π.χ. Κώστας / Τεχνικός")

            cu1, cu2 = st.columns(2)
            with cu1:
                new_status = st.selectbox("Νέα Κατάσταση:", ["Open", "In Progress", "Pending", "Resolved", "Closed"], index=["Open", "In Progress", "Pending", "Resolved", "Closed"].index(t_data['status']))
                add_materials = st.text_input("Επιπλέον Υλικά / Ενέργειες:")
                add_cost = st.number_input("Επιπλέον Κόστος Υλικών (€):", min_value=0.0, step=10.0)
                res_time = st.number_input("Πραγματικές Ώρες Αποκατάστασης:", min_value=0.0, value=float(t_data['resolution_time_hrs'] or 0.0), step=0.5)
            with cu2:
                comment = st.text_area("Σχόλιο / Πρόοδος Εργασιών:")
                new_photos = st.file_uploader("Προσθήκη Φωτογραφιών Αποκατάστασης (After):", type=["jpg", "png", "heic"], accept_multiple_files=True)

            if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης"):
                updater_full = f"{updater_name} ({updater_role})" if updater_name else updater_role
                total_cost = float(t_data.get('material_cost', 0.0) or 0.0) + add_cost
                
                upd_payload = {
                    "status": new_status,
                    "resolution_time_hrs": res_time,
                    "material_cost": total_cost,
                    "materials_used": f"{t_data['materials_used']} | {add_materials}" if add_materials else t_data['materials_used']
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
