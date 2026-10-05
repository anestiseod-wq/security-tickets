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
    initial_sidebar_state="collapsed"
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
# 2. MODERN HIGH-CONTRAST MOBILE THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }
    
    .stApp { 
        background-color: #0b1329; 
        color: #f8fafc; 
        font-family: 'Inter', system-ui, -apple-system, sans-serif; 
    }
    
    .pmi-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #0284c7 100%);
        padding: 22px 26px;
        border-radius: 16px;
        border: 1px solid #38bdf8;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px !important;
    }
    
    label { color: #e2e8f0 !important; font-weight: 700 !important; font-size: 0.95rem !important; }

    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 16px; 
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; font-size: 0.9rem; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 1.6rem; }

    /* Big Action Nav Buttons */
    .big-nav-btn button {
        height: 60px !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 12px 20px !important;
    }
    
    .full-card {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-left: 6px solid #38bdf8;
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 20px;
        width: 100%;
    }

    .success-banner {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        padding: 16px;
        border-radius: 12px;
        color: #6ee7b7;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .audit-box {
        background-color: #1e293b;
        border: 1px solid #475569;
        padding: 15px;
        border-radius: 10px;
        color: #f8fafc;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Μετατροπή Αρχείου Εικόνας σε Base64
def get_b64_img(file):
    if file is not None:
        try:
            b_data = file.getvalue()
            if not b_data:
                return None
            encoded = base64.b64encode(b_data).decode()
            mime = getattr(file, 'type', 'image/jpeg') or 'image/jpeg'
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return None
    return None

# ---------------------------------------------------------
# 3. DATA RETRIEVAL (FRESH FROM SUPABASE)
# ---------------------------------------------------------
def fetch_data():
    try:
        tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

df_tickets = fetch_data()
HOURLY_RATE = 25.0  # €/ώρα εργασίας τεχνικού

if not df_tickets.empty:
    df_tickets["created_dt"] = pd.to_datetime(df_tickets["created_at"], errors="coerce").dt.tz_localize(None)
    df_tickets["Έτος"] = df_tickets["created_dt"].dt.year.fillna(datetime.now().year).astype(int)
    df_tickets["Μήνας_Num"] = df_tickets["created_dt"].dt.month.fillna(datetime.now().month).astype(int)
    
    month_names = {1: "Ιανουάριος", 2: "Φεβρουάριος", 3: "Μάρτιος", 4: "Απρίλιος", 5: "Μάιος", 6: "Ιούνιος",
                   7: "Ιούλιος", 8: "Αύγουστος", 9: "Σεπτέμβριος", 10: "Οκτώβριος", 11: "Νοέμβριος", 12: "Δεκέμβριος"}
    df_tickets["Μήνας"] = df_tickets["Μήνας_Num"].map(month_names)

    if "resolution_time_hrs" in df_tickets.columns:
        df_tickets["resolution_time_hrs"] = pd.to_numeric(df_tickets["resolution_time_hrs"], errors="coerce").fillna(0.0)

# ---------------------------------------------------------
# 4. SESSION STATE
# ---------------------------------------------------------
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "home"
if "active_ticket_id" not in st.session_state:
    st.session_state.active_ticket_id = None
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

# ---------------------------------------------------------
# 5. HEADER
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Papastratos (PMI) - Security Maintenance Hub
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 600;">
                    Κεντρική Διαχείριση Βλαβών, Πλήρες Ιστορικό, Υπολογισμός Κόστους & Ημερών
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.8); padding: 8px 16px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800;">● SYSTEM ACTIVE</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.success_msg:
    st.markdown(f'<div class="success-banner">{st.session_state.success_msg}</div>', unsafe_allow_html=True)
    st.session_state.success_msg = None

# ---------------------------------------------------------
# 6. ΚΟΥΜΠΙΑ ΠΛΟΗΓΗΣΗΣ
# ---------------------------------------------------------
nav_c1, nav_c2, nav_c3 = st.columns(3)
with nav_c1:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("🏠 Αρχική Σελίδα & KPIs"):
        st.session_state.view_mode = "home"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_c2:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("➕ Νέα Καταχώρηση Βλάβης"):
        st.session_state.view_mode = "new_ticket"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_c3:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("📋 Λίστα & Ιστορικό Βλαβών"):
        st.session_state.view_mode = "list_tickets"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. ΟΘΟΝΗ 1: ΑΡΧΙΚΗ & ΣΥΝΟΛΙΚΑ KPIs
# ---------------------------------------------------------
if st.session_state.view_mode == "home":
    st.subheader("📊 Κεντρικά Σύνολα, KPIs & Κόστη")
    
    if not df_tickets.empty:
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            years_available = ["Όλα τα Έτη"] + sorted(list(df_tickets["Έτος"].unique()), reverse=True)
            sel_year = st.selectbox("📅 Επιλογή Έτους:", years_available)
        with f_col2:
            sel_month = st.selectbox("📆 Επιλογή Μήνα:", ["Όλοι οι Μήνες"] + list(month_names.values()))

        filtered_home_df = df_tickets.copy()
        if sel_year != "Όλα τα Έτη":
            filtered_home_df = filtered_home_df[filtered_home_df["Έτος"] == int(sel_year)]
        if sel_month != "Όλοι οι Μήνες":
            filtered_home_df = filtered_home_df[filtered_home_df["Μήνας"] == sel_month]

        tot_tck = len(filtered_home_df)
        op_tck = len(filtered_home_df[filtered_home_df["status"] == "Open"])
        pend_tck = len(filtered_home_df[filtered_home_df["status"] == "Pending"])
        cl_tck = len(filtered_home_df[filtered_home_df["status"] == "Closed"])
        
        tot_hrs = float(filtered_home_df["resolution_time_hrs"].sum()) if "resolution_time_hrs" in filtered_home_df.columns else 0.0
        tot_labor_cost = tot_hrs * HOURLY_RATE

        closed_df = filtered_home_df[filtered_home_df["status"] == "Closed"].copy()
        avg_days = 0.0
        if not closed_df.empty:
            closed_df["c_dt"] = pd.to_datetime(closed_df["created_at"], errors="coerce").dt.tz_localize(None)
            closed_df["dur_days"] = (datetime.now() - closed_df["c_dt"]).dt.total_seconds() / 86400.0
            avg_days = max(0.0, float(closed_df["dur_days"].mean()))

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Σύνολο Βλαβών", tot_tck)
        k2.metric("🔴 Open", op_tck)
        k3.metric("🟡 Pending", pend_tck)
        k4.metric("🟢 Closed", cl_tck)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("⏱️ Σύνολο Ωρών Εργασίας", f"{tot_hrs:.1f} hrs")
        c2.metric("💰 Σύνολο Κόστους Εργασίας (€25/h)", f"€{tot_labor_cost:,.2f}")
        c3.metric("📅 Μέσος Χρόνος Αποκατάστασης (MTTR)", f"{avg_days:.1f} ημέρες")

        st.markdown("---")
        st.subheader("📊 Ανάλυση Βλαβών & Ωρών ανά Τμήμα")
        if "category" in filtered_home_df.columns:
            dept_summary = filtered_home_df.groupby("category").agg(
                Βλάβες=("ticket_id", "count"),
                Σύνολο_Ωρών=("resolution_time_hrs", "sum")
            ).reset_index()
            st.dataframe(dept_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένες βλάβες στη βάση.")

# ---------------------------------------------------------
# 8. ΟΘΟΝΗ 2: ΝΕΑ ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ
# ---------------------------------------------------------
elif st.session_state.view_mode == "new_ticket":
    st.subheader("📝 Φόρμα Καταχώρησης Νέας Βλάβης")
    
    with st.form("new_ticket_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tck_id = st.text_input("Κωδικός Ticket", value=f"TCK-{datetime.now().strftime('%m%d-%H%M')}")
            creator_tech = st.text_input("👤 Ονοματεπώνυμο Χρήστη / Τεχνικού", placeholder="π.χ. Ανέστης Θεοδωρίδης")
            user_role = st.selectbox("🎭 Ρόλος / Ειδικότητα", ["Security Systems Admin", "Technical Expert", "G4S Security Officer", "Shift Supervisor", "External Contractor"])
            category = st.selectbox("Τμήμα / Κατηγορία", ["CCTV (Κάμερες)", "ACS (Access Control / Τουρνικέ)", "Fire Alarm (Πυρανίχνευση)", "Network / PoE / Fiber", "Άλλο"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Είσοδος Τουρνικέ DR_116")

        with f2:
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. Cam 20 / Reader CR.08L0.01.01")
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "Pending", "Closed"])
            duration_hrs = st.number_input("⏱️ Αρχικές Ώρες Εργασίας (hrs)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
            materials = st.text_area("🛠️ Περιγραφή Υλικών / Ανταλλακτικών", placeholder="π.χ. 1x PoE Injector, 10m UTP Cat6, 2x RJ45")

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή της βλάβης...")

        st.markdown("##### 📁 Επιλογή Αρχείου Φωτογραφίας (Προαιρετικό)")
        upload_photo = st.file_uploader("Μεταφόρτωση Εικόνας", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("💾 Αποθήκευση Βλάβης στη Βάση"):
            photo_b64 = get_b64_img(upload_photo)
            
            now_stamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            role_str = f"[{user_role}]" if user_role else ""
            creator_prefix = f"[{now_stamp} - Καταχώρηση: {creator_tech} {role_str}]\n" if creator_tech.strip() else f"[{now_stamp} - Νέα Καταχώρηση]\n"
            
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
            
            try:
                supabase.table("tickets").insert(insert_payload).execute()
                st.session_state.success_msg = f"✅ Η βλάβη **{tck_id}** καταχωρήθηκε επιτυχώς!"
                st.session_state.view_mode = "home"
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Σφάλμα καταχώρησης: {e}")

# ---------------------------------------------------------
# 9. ΟΘΟΝΗ 3: ΛΙΣΤΑ ΒΛΑΒΩΝ & FULL-WIDTH DETAIL VIEW
# ---------------------------------------------------------
elif st.session_state.view_mode == "list_tickets":
    
    if st.session_state.active_ticket_id and not df_tickets.empty:
        selected_row = df_tickets[df_tickets["ticket_id"] == st.session_state.active_ticket_id]
        
        if not selected_row.empty:
            row = selected_row.iloc[0]
            
            if st.button("⬅️ Επιστροφή στη Λίστα Όλων των Βλαβών"):
                st.session_state.active_ticket_id = None
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            badge_color = "#ef4444" if row['status'] == "Open" else ("#f59e0b" if row['status'] == "Pending" else "#10b981")
            
            c_dt = pd.to_datetime(row.get('created_at'), errors='coerce')
            if pd.notnull(c_dt):
                c_dt = c_dt.tz_localize(None)
                open_days = max(0, (datetime.now() - c_dt).days)
            else:
                open_days = 0

            lab_cost = float(row.get('resolution_time_hrs', 0.0) or 0.0) * HOURLY_RATE

            st.markdown(f"""
            <div class="full-card" style="border-left-color: {badge_color};">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <h2 style="margin:0; color:#38bdf8;">📌 {row['ticket_id']} — {row['category']}</h2>
                    <span style="background:{badge_color}; color:#ffffff; padding:6px 16px; border-radius:8px; font-weight:800; font-size:1.1rem;">{row['status']}</span>
                </div>
                <hr style="border-color:#334155; margin:15px 0;">
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div><b>📍 Περιοχή / Κτίριο:</b> <br><span style="color:#f8fafc; font-size:1.1rem;">{row['building_area']}</span></div>
                    <div><b>🖥️ Συσκευή / Asset:</b> <br><span style="color:#f8fafc; font-size:1.1rem;">{row['device_asset']}</span></div>
                    <div><b>🚨 Προτεραιότητα:</b> <br><span style="color:#f8fafc; font-size:1.1rem;">{row['priority']}</span></div>
                    <div><b>⏱️ Ώρες Εργασίας:</b> <br><span style="color:#38bdf8; font-size:1.1rem; font-weight:800;">{row.get('resolution_time_hrs', 0.0)} hrs</span></div>
                    <div><b>📅 Ημέρες Ανοιχτή:</b> <br><span style="color:#f59e0b; font-size:1.1rem; font-weight:800;">{open_days} ημέρες</span></div>
                    <div><b>💰 Κόστος Εργασίας:</b> <br><span style="color:#10b981; font-size:1.1rem; font-weight:800;">€{lab_cost:,.2f}</span></div>
                </div>
                <hr style="border-color:#334155; margin:15px 0;">
                <div><b>🛠️ Περιγραφή Υλικών:</b><br><span style="color:#cbd5e1; font-size:1.05rem;">{row.get('materials_used', 'N/A')}</span></div>
            </div>
            """, unsafe_allow_html=True)

            photo_val = row.get('photo_url', None)
            if photo_val and str(photo_val).strip():
                st.markdown("##### 📸 Φωτογραφία Βλάβης")
                try:
                    st.image(photo_val, use_column_width=True)
                except Exception:
                    st.info("Δεν ήταν δυνατή η προεπισκόπηση της φωτογραφίας.")

            st.markdown("##### 📜 Πλήρες Ιστορικό Ενεργειών & Audit Trail")
            st.markdown(f'<div class="audit-box">{row["description"]}</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("##### 🔄 Φόρμα Ενημέρωσης & Κλεισίματος Βλάβης")
            
            u1, u2, u3 = st.columns(3)
            with u1:
                tech_name = st.text_input("👤 Ονοματεπώνυμο", placeholder="Ονοματεπώνυμο")
            with u2:
                up_role = st.selectbox("🎭 Ρόλος", ["Security Systems Admin", "Technical Expert", "G4S Security Officer", "Shift Supervisor", "External Contractor"])
            with u3:
                st_options = ["Open", "Pending", "Closed"]
                curr_st_idx = st_options.index(row['status']) if row['status'] in st_options else 0
                up_status = st.selectbox("Κατάσταση", st_options, index=curr_st_idx)

            up_hours = st.number_input("⏱️ Σύνολο Ωρών (hrs)", min_value=0.0, max_value=200.0, value=float(row.get('resolution_time_hrs', 0.0) or 0.0), step=0.5)
            up_mats = st.text_area("🛠️ Περιγραφή Υλικών / Ανταλλακτικών", value=str(row.get('materials_used', '') or ''))
            new_notes = st.text_area("✍️ Προσθήκη Νέων Ενεργειών / Σημειώσεων", placeholder="Γράψτε τις νέες ενέργειες που πραγματοποιήθηκαν...")

            st.markdown("##### 📁 Προσθήκη / Αλλαγή Αρχείου Εικόνας")
            up_file = st.file_uploader("Νέο Αρχείο Εικόνας", type=["jpg", "jpeg", "png"])

            if st.button("💾 Αποθήκευση Ενημέρωσης στη Βάση"):
                now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
                t_prefix = f"[{now_str} - Χρήστης: {tech_name} ({up_role})]" if tech_name.strip() else f"[{now_str} - Ενημέρωση]"
                
                # Προσθήκη νέου ιστορικού στο παλιό
                old_desc = str(row['description']) if pd.notnull(row['description']) else ""
                if new_notes.strip():
                    updated_desc = f"{old_desc}\n\n{t_prefix}:\n{new_notes.strip()}"
                elif tech_name.strip():
                    updated_desc = f"{old_desc}\n\n{t_prefix}: Αλλαγή κατάστασης σε {up_status}."
                else:
                    updated_desc = old_desc

                payload = {
                    "status": up_status,
                    "resolution_time_hrs": float(up_hours),
                    "materials_used": up_mats,
                    "description": updated_desc
                }

                if up_file is not None:
                    new_b64 = get_b64_img(up_file)
                    if new_b64:
                        payload["photo_url"] = new_b64

                try:
                    supabase.table("tickets").update(payload).eq("ticket_id", row['ticket_id']).execute()
                    st.session_state.success_msg = f"✅ Η βλάβη **{row['ticket_id']}** ενημερώθηκε επιτυχώς!"
                    st.session_state.view_mode = "home"
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Σφάλμα ενημέρωσης: {e}")

    else:
        st.subheader("📋 Λίστα Όλων των Βλαβών (Πατήστε σε μια βλάβη για ανάλυση)")
        
        if not df_tickets.empty:
            c1, c2, c3 = st.columns(3)
            with c1:
                status_filter = st.selectbox("Κατάσταση:", ["Όλες οι Βλάβες", "🔴 Ανοιχτές (Open & Pending)", "🟢 Ολοκληρωμένες (Closed)"])
            with c2:
                years_list = ["Όλα τα Έτη"] + sorted(list(df_tickets["Έτος"].unique()), reverse=True)
                year_filter = st.selectbox("Έτος:", years_list)
            with c3:
                search_txt = st.text_input("🔍 Αναζήτηση:", placeholder="Κωδικός, περιοχή, συσκευή...")

            display_df = df_tickets.copy()
            if status_filter == "🔴 Ανοιχτές (Open & Pending)":
                display_df = display_df[display_df["status"] != "Closed"]
            elif status_filter == "🟢 Ολοκληρωμένες (Closed)":
                display_df = display_df[display_df["status"] == "Closed"]

            if year_filter != "Όλα τα Έτη":
                display_df = display_df[display_df["Έτος"] == int(year_filter)]

            if search_txt:
                display_df = display_df[
                    display_df["ticket_id"].str.contains(search_txt, case=False, na=False) |
                    display_df["building_area"].str.contains(search_txt, case=False, na=False) |
                    display_df["device_asset"].str.contains(search_txt, case=False, na=False)
                ]

            st.markdown(f"**Βρέθηκαν {len(display_df)} βλάβες:**")
            st.markdown("---")

            for _, row in display_df.iterrows():
                badge_icon = "🔴" if row['status'] == "Open" else ("🟡" if row['status'] == "Pending" else "🟢")
                btn_label = f"{badge_icon} [{row['status']}] {row['ticket_id']} — {row['building_area']} ({row['category']})"
                
                if st.button(btn_label, key=f"btn_{row['ticket_id']}"):
                    st.session_state.active_ticket_id = row['ticket_id']
                    st.rerun()
        else:
            st.info("Δεν υπάρχουν καταχωρημένες βλάβες στη βάση.")
