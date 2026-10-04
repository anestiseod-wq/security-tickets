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

# Σύνδεση με Supabase μέσω Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Σφάλμα σύνδεσης με τη βάση Supabase. Ελέγξτε τα Secrets στο Streamlit Cloud.")
    st.stop()

# ---------------------------------------------------------
# 2. MODERN HIGH-CONTRAST SOC THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* General Background & Text Colors */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', system-ui, sans-serif;
    }
    
    /* PMI Modern Glassmorphism Header */
    .pmi-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 50%, rgba(2, 132, 199, 0.8) 100%);
        backdrop-filter: blur(12px);
        padding: 24px 30px;
        border-radius: 18px;
        border: 1px solid rgba(56, 189, 248, 0.4);
        margin-bottom: 25px;
        box-shadow: 0 10px 30px -5px rgba(2, 132, 199, 0.3);
    }
    
    /* Input Fields Fix - High Contrast for Laptops */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        font-size: 0.98rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 8px rgba(56, 189, 248, 0.4) !important;
    }
    
    /* Label Fix */
    label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }

    /* KPI Metric Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; }

    /* Action Buttons */
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

    /* Modern History Cards */
    .history-card {
        background: #1e293b;
        border-left: 5px solid #38bdf8;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-radius: 8px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    
    /* Form Container */
    div[data-testid="stForm"] {
        background-color: #0f172a;
        border: 1px solid #334155;
        padding: 24px;
        border-radius: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------
def generate_ticket_id():
    """Αυτόματη αρίθμηση TCK-0001, TCK-0002..."""
    try:
        res = supabase.table("tickets").select("id").order("id", desc=True).limit(1).execute()
        if res.data:
            next_num = res.data[0]['id'] + 1
        else:
            next_num = 1
    except Exception:
        next_num = 1
    return f"TCK-{next_num:04d}"

def upload_photos_to_supabase(files, ticket_id, photo_type="BEFORE"):
    """Μεταφόρτωση φωτογραφιών στο Supabase Storage & εγγραφή στο DB"""
    urls = []
    for idx, file in enumerate(files):
        if file is not None:
            file_ext = file.name.split('.')[-1] if hasattr(file, 'name') and file.name else 'jpg'
            file_path = f"{ticket_id}/{photo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}.{file_ext}"
            
            file_bytes = file.getvalue()
            supabase.storage.from_("ticket-photos").upload(
                file_path, 
                file_bytes, 
                file_options={"content-type": f"image/{file_ext}"}
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
                <h1 style="margin:0; font-size: 2.2rem; color: #ffffff !important; font-weight: 800; letter-spacing: -0.5px;">
                    🛡️ PMI Miscellaneous Issues
                </h1>
                <p style="margin:6px 0 0 0; color: #38bdf8; font-size: 1.05rem; font-weight: 500;">
                    Security Systems, Infrastructure & Site Maintenance Operations
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.7); padding: 10px 18px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800; font-size: 0.95rem;">● LIVE DATABASECONNECTED</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Ανάκτηση δεδομένων από Supabase
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

total_tck = len(df_tickets)
open_tck = len(df_tickets[df_tickets["status"].isin(["Open", "In Progress", "Pending"])]) if not df_tickets.empty else 0
critical_tck = len(df_tickets[(df_tickets["priority"] == "Critical") & (df_tickets["status"] != "Closed")]) if not df_tickets.empty else 0
mttr = df_tickets[df_tickets["status"] == "Closed"]["resolution_time_hrs"].mean() if not df_tickets.empty and "resolution_time_hrs" in df_tickets.columns else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Συνολικά Tickets", total_tck)
col2.metric("Ανοιχτά / Σε εξέλιξη", open_tck)
col3.metric("Critical Εκκρεμή", critical_tck, delta="⚠️ Απαιτείται Ενέργεια" if critical_tck > 0 else "✅ Ομαλό", delta_color="inverse")
col4.metric("MTTR (Μ.Ο. Επισκευής)", f"{mttr:.1f} hrs" if pd.notnull(mttr) else "0.0 hrs")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS: ΔΗΜΙΟΥΡΓΙΑ - ΠΙΝΑΚΑΣ - ΚΑΡΤΕΛΑ TICKET
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 Νέο Ticket Βλάβης", "📊 Πίνακας & Φίλτρα", "🔍 Αναλυτική Καρτέλα & Χάρτης"])

# TAB 1: ΝΕΟ TICKET
with tab1:
    st.subheader("Καταγραφή Νέου Περιστατικού & Τοποθεσία")
    with st.form("new_ticket_form", clear_on_submit=True):
        st.markdown("##### 👤 Στοιχεία Συντάκτη / Υπογραφή")
        cs1, cs2 = st.columns(2)
        with cs1:
            author_role = st.selectbox("Ρόλος Συντάκτη", ["Τεχνικός Ασφαλείας / Security Tech", "IT Support / Network Expert", "Supervisor / Team Lead", "Site Security / SOC Operator", "Εξωτερικός Εργολάβος / Vendor"])
        with cs2:
            author_name = st.text_input("Ονοματεπώνυμο Χειριστή", placeholder="π.χ. Ανέστης Θεοδωρίδης")

        st.markdown("---")
        st.markdown("##### 🛠️ Στοιχεία Βλάβης")
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

        st.markdown("---")
        st.markdown("##### 📍 Γεωγραφικός Εντοπισμός (Χάρτης)")
        cm1, cm2 = st.columns(2)
        with cm1:
            lat = st.number_input("Γεωγραφικό Πλάτος (Latitude)", value=38.0333, format="%.6f")
        with cm2:
            lon = st.number_input("Γεωγραφικό Μήκος (Longitude)", value=23.5833, format="%.6f")

        st.markdown("##### 📸 Φωτογραφίες Βλάβης (Before)")
        up_files = st.file_uploader("Επιλογή από Gallery/Αρχεία (Πολλαπλά)", type=["jpg", "png", "heic"], accept_multiple_files=True)
        cam_file = st.camera_input("Ή Λήψη από Κάμερα Κινητού")

        if st.form_submit_button("💾 Δημιουργία Ticket"):
            t_id = generate_ticket_id()
            full_author = f"{author_name} ({author_role})" if author_name else author_role
            
            # 1. Εγγραφή Ticket
            new_ticket = {
                "ticket_id": t_id,
                "category": category,
                "building_area": f"{building_area} [{floor_level}]",
                "device_asset": device_asset,
                "priority": priority,
                "status": status,
                "description": f"[{full_author}]: {description}",
                "materials_used": materials
            }
            supabase.table("tickets").insert(new_ticket).execute()

            # 2. Upload Φωτογραφιών
            all_files = (up_files if up_files else []) + ([cam_file] if cam_file else [])
            if all_files:
                upload_photos_to_supabase(all_files, t_id, photo_type="BEFORE")

            # 3. Εγγραφή στο Ιστορικό (Audit Trail)
            supabase.table("ticket_updates").insert({
                "ticket_id": t_id,
                "status_changed_to": status,
                "comment": f"Αρχική καταγραφή βλάβης από τον/την {full_author}.",
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
            filtered_df[["ticket_id", "created_at", "category", "building_area", "device_asset", "priority", "status"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Δεν υπάρχουν καταχωρημένα tickets στη βάση.")

# TAB 3: ΑΝΑΛΥΤΙΚΗ ΚΑΡΤΕΛΑ TICKET, ΧΑΡΤΗΣ & UPDATE
with tab3:
    st.subheader("🔍 Αναλυτική Διαχείριση Ticket & Τοποθεσία")
    if not df_tickets.empty:
        selected_tck_id = st.selectbox("Επιλέξτε Ticket ID για προβολή/ενημέρωση:", options=df_tickets["ticket_id"].tolist())
        
        # Ανάκτηση στοιχείων Ticket
        t_data = supabase.table("tickets").select("*").eq("ticket_id", selected_tck_id).single().execute().data
        p_data = supabase.table("ticket_photos").select("*").eq("ticket_id", selected_tck_id).execute().data
        u_data = supabase.table("ticket_updates").select("*").eq("ticket_id", selected_tck_id).order("created_at", desc=True).execute().data

        col_info, col_map = st.columns([1, 1])
        
        with col_info:
            st.markdown(f"### 📌 {t_data['ticket_id']} - {t_data['category']}")
            st.write(f"**Περιοχή / Όροφος:** {t_data['building_area']}")
            st.write(f"**Συσκευή:** {t_data['device_asset']}")
            st.write(f"**Προτεραιότητα:** `{t_data['priority']}` | **Κατάσταση:** `{t_data['status']}`")
            st.write(f"**Περιγραφή:** {t_data['description']}")
            st.write(f"**Υλικά:** {t_data['materials_used']}")
            st.caption(f"Ημερομηνία Δημιουργίας: {t_data['created_at']}")

        with col_map:
            st.markdown("### 🗺️ Εντοπισμός στο Χάρτη")
            # Προεπιλεγμένες συντεταγμένες Ασπροπύργου/Facility αν δεν οριστούν
            map_data = pd.DataFrame({
                'lat': [38.0333],
                'lon': [23.5833]
            })
            st.map(map_data, zoom=14)

        st.markdown("---")
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
        
        # ΦΟΡΜΑ ΕΝΗΜΕΡΩΣΗΣ (UPDATES)
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
                res_time = st.number_input("Ώρες Αποκατάστασης (αν έκλεισε):", min_value=0.0, value=float(t_data['resolution_time_hrs'] or 0.0), step=0.5)
            with cu2:
                comment = st.text_area("Σχόλιο / Πρόοδος Εργασιών:")
                new_photos = st.file_uploader("Προσθήκη Φωτογραφιών Αποκατάστασης (After):", type=["jpg", "png", "heic"], accept_multiple_files=True)

            if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης"):
                updater_full = f"{updater_name} ({updater_role})" if updater_name else updater_role
                
                # 1. Update Ticket Table
                upd_payload = {
                    "status": new_status,
                    "resolution_time_hrs": res_time,
                    "materials_used": f"{t_data['materials_used']} | {add_materials}" if add_materials else t_data['materials_used']
                }
                if new_status == "Closed":
                    upd_payload["closed_at"] = datetime.now().isoformat()
                
                supabase.table("tickets").update(upd_payload).eq("ticket_id", selected_tck_id).execute()

                # 2. Upload After Photos
                if new_photos:
                    upload_photos_to_supabase(new_photos, selected_tck_id, photo_type="AFTER")

                # 3. Log Audit Trail
                supabase.table("ticket_updates").insert({
                    "ticket_id": selected_tck_id,
                    "status_changed_to": new_status,
                    "comment": f"[{updater_full}]: {comment if comment else 'Ενημέρωση στοιχείων.'}",
                    "action_type": "UPDATE"
                }).execute()

                st.success(f"✅ Το Ticket ενημερώθηκε επιτυχώς από τον/την {updater_full}!")
                st.rerun()

        # AUDIT TRAIL / ΙΣΤΟΡΙΚΟ
        st.markdown("### 📜 Ιστορικό Ενεργειών (Audit Trail)")
        if u_data:
            for log in u_data:
                st.markdown(f"""
                <div class="history-card">
                    <small style="color:#38bdf8;"><b>{log['created_at']}</b> — Status: <span style="color:#10b981;"><b>{log['status_changed_to']}</b></span></small><br>
                    <span style="color:#f1f5f9; font-size:1.02rem;">{log['comment']}</span>
                </div>
                """, unsafe_allow_html=True)
