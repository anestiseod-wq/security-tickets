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
# 2. MODERN HIGH-CONTRAST MOBILE-FRIENDLY THEME (CSS)
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

    /* Big Action Buttons */
    .big-nav-btn button {
        height: 65px !important;
        font-size: 1.15rem !important;
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
    
    div[data-testid="stForm"] { 
        background-color: #1e293b; 
        border: 1px solid #334155; 
        padding: 24px; 
        border-radius: 16px; 
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

    .success-alert-box {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        padding: 18px;
        border-radius: 12px;
        color: #6ee7b7;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def get_b64_img(file):
    if file is not None:
        try:
            b_data = file.getvalue()
            encoded = base64.b64encode(b_data).decode()
            mime = getattr(file, 'type', 'image/jpeg') or 'image/jpeg'
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return None
    return None

# ---------------------------------------------------------
# 3. DATA RETRIEVAL & ALL KPIs CALCULATIONS
# ---------------------------------------------------------
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

HOURLY_RATE = 25.0  # €/ώρα εργασίας τεχνικού

total_tck = len(df_tickets)
open_tck = len(df_tickets[df_tickets["status"] == "Open"]) if not df_tickets.empty else 0
pending_tck = len(df_tickets[df_tickets["status"] == "Pending"]) if not df_tickets.empty else 0
closed_tck = len(df_tickets[df_tickets["status"] == "Closed"]) if not df_tickets.empty else 0

total_hours = 0.0
total_labor_cost = 0.0
total_mat_cost = 0.0
total_cost = 0.0
avg_days_to_close = 0.0

if not df_tickets.empty:
    # Ώρες & Κόστος Εργασίας
    if "resolution_time_hrs" in df_tickets.columns:
        df_tickets["resolution_time_hrs"] = pd.to_numeric(df_tickets["resolution_time_hrs"], errors="coerce").fillna(0.0)
        total_hours = float(df_tickets["resolution_time_hrs"].sum())
        total_labor_cost = total_hours * HOURLY_RATE

    # Κόστος Υλικών (αν υπάρχει στήλη material_cost)
    if "material_cost" in df_tickets.columns:
        df_tickets["material_cost"] = pd.to_numeric(df_tickets["material_cost"], errors="coerce").fillna(0.0)
        total_mat_cost = float(df_tickets["material_cost"].sum())
    
    total_cost = total_labor_cost + total_mat_cost

    # Υπολογισμός Μέσου Χρόνου Αποκατάστασης (MTTR)
    if "created_at" in df_tickets.columns:
        df_tickets["created_dt"] = pd.to_datetime(df_tickets["created_at"], errors="coerce").dt.tz_localize(None)
        
        # Αν υπάρχει updated_at χρησιμοποιούμε αυτό, αλλιώς created_at
        if "updated_at" in df_tickets.columns:
            df_tickets["updated_dt"] = pd.to_datetime(df_tickets["updated_at"], errors="coerce").dt.tz_localize(None)
        else:
            df_tickets["updated_dt"] = df_tickets["created_dt"]

        closed_df = df_tickets[df_tickets["status"] == "Closed"].copy()
        if not closed_df.empty:
            closed_df["duration_days"] = (closed_df["updated_dt"] - closed_df["created_dt"]).dt.total_seconds() / 86400.0
            avg_days_to_close = max(0.0, float(closed_df["duration_days"].mean()))

# ---------------------------------------------------------
# 4. HEADER & DASHBOARD METRICS
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Papastratos (PMI) - Security Maintenance Hub
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.02rem; font-weight: 600;">
                    Κεντρικός Πίνακας KPIs, Κόστη Εργασίας & Υλικών, Ιστορικό & Αποκατάσταση ανά Τμήμα
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.8); padding: 8px 16px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800;">● SYSTEM ACTIVE</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# KPIs SUMMARY BANNER
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("🔴 Ανοιχτές", open_tck)
m2.metric("🟢 Κλειστές", closed_tck)
m3.metric("⏱️ Ώρες Εργασίας", f"{total_hours:.1f}h")
m4.metric("💰 Κόστος Εργασίας", f"€{total_labor_cost:,.0f}")
m5.metric("🛠️ Κόστος Υλικών", f"€{total_mat_cost:,.0f}")
m6.metric("📅 Μ.Ο. Αποκατάστασης", f"{avg_days_to_close:.1f} μέρες")

st.markdown("<br>", unsafe_allow_html=True)

# Session state για διαχείριση προβολών
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "home"
if "active_ticket_id" not in st.session_state:
    st.session_state.active_ticket_id = None
if "last_created_ticket" not in st.session_state:
    st.session_state.last_created_ticket = None

# ---------------------------------------------------------
# 5. ΜΕΓΑΛΑ ΚΟΥΜΠΙΑ ΠΛΟΗΓΗΣΗΣ ΣΤΗΝ ΑΡΧΙΚΗ
# ---------------------------------------------------------
btn_c1, btn_c2 = st.columns(2)
with btn_c1:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("➕ Νέα Καταχώρηση Βλάβης"):
        st.session_state.view_mode = "new_ticket"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with btn_c2:
    st.markdown('<div class="big-nav-btn">', unsafe_allow_html=True)
    if st.button("📋 Λίστα & Ιστορικό Βλαβών"):
        st.session_state.view_mode = "list_tickets"
        st.session_state.active_ticket_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. ΟΘΟΝΗ 1: ΝΕΑ ΚΑΤΑΧΩΡΗΣΗ ΒΛΑΒΗΣ
# ---------------------------------------------------------
if st.session_state.view_mode == "new_ticket":
    st.subheader("📝 Φόρμα Καταχώρησης Νέας Βλάβης")
    
    # Ειδοποίηση αν μόλις καταχωρήθηκε βλάβη
    if st.session_state.last_created_ticket:
        st.markdown(f"""
        <div class="success-alert-box">
            <h4>✅ Επιτυχής Καταχώρηση!</h4>
            <p>Το Ticket <b>{st.session_state.last_created_ticket}</b> αποθηκεύτηκε στη βάση δεδομένων PMI.</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.last_created_ticket = None

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
            mat_cost_val = st.number_input("🛠️ Εκτιμώμενο Κόστος Υλικών (€)", min_value=0.0, max_value=10000.0, value=0.0, step=10.0)
            materials = st.text_area("🛠️ Περιγραφή Υλικών / Ανταλλακτικών", placeholder="π.χ. 1x PoE Injector, 10m UTP Cat6, 2x RJ45")

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή της βλάβης...")

        st.markdown("##### 📸 Φωτογραφία Βλάβης (Προαιρετικό)")
        cam_col, file_col = st.columns(2)
        with cam_col:
            cam_photo = st.camera_input("📷 Λήψη από Κάμερα")
        with file_col:
            upload_photo = st.file_uploader("📁 Επιλογή Αρχείου Εικόνας", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("💾 Αποθήκευση Βλάβης στη Βάση"):
            active_photo = cam_photo if cam_photo is not None else upload_photo
            photo_b64 = get_b64_img(active_photo)
            
            role_str = f"[{user_role}]" if user_role else ""
            creator_prefix = f"[Καταχώρηση: {creator_tech} {role_str}]\n" if creator_tech.strip() else ""
            
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
                st.session_state.last_created_ticket = tck_id
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Σφάλμα καταχώρησης: {e}")

# ---------------------------------------------------------
# 7. ΟΘΟΝΗ 2: ΛΙΣΤΑ ΒΛΑΒΩΝ & ΑΝΑΛΥΤΙΚΗ ΠΡΟΒΟΛΗ (FULL-WIDTH)
# ---------------------------------------------------------
elif st.session_state.view_mode == "list_tickets":
    
    # ΑΝ ΕΧΕΙ ΕΠΙΛΕΓΕΙ ΣΥΓΚΕΚΡΙΜΕΝΗ ΒΛΑΒΗ -> FULL WIDTH VIEW
    if st.session_state.active_ticket_id and not df_tickets.empty:
        selected_row = df_tickets[df_tickets["ticket_id"] == st.session_state.active_ticket_id]
        
        if not selected_row.empty:
            row = selected_row.iloc[0]
            
            if st.button("⬅️️ Επιστροφή στη Λίστα Όλων των Βλαβών"):
                st.session_state.active_ticket_id = None
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            badge_color = "#ef4444" if row['status'] == "Open" else ("#f59e0b" if row['status'] == "Pending" else "#10b981")
            
            # Ασφαλής υπολογισμός ημερών
            c_dt = pd.to_datetime(row.get('created_at'), errors='coerce')
            if pd.notnull(c_dt):
                c_dt = c_dt.tz_localize(None)
                u_dt = pd.to_datetime(row.get('updated_at', datetime.now()), errors='coerce')
                u_dt = u_dt.tz_localize(None) if pd.notnull(u_dt) else datetime.now()
                open_days = max(0, (u_dt - c_dt).days)
            else:
                open_days = 0

            # FULL-WIDTH CARD
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
                    <div><b>💰 Κόστος Εργασίας:</b> <br><span style="color:#10b981; font-size:1.1rem; font-weight:800;">€{(float(row.get('resolution_time_hrs', 0.0) or 0.0) * HOURLY_RATE):,.2f}</span></div>
                </div>
                <hr style="border-color:#334155; margin:15px 0;">
                <div><b>🛠️ Υλικά & Ανταλλακτικά:</b><br><span style="color:#cbd5e1; font-size:1.05rem;">{row.get('materials_used', 'N/A')}</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Φωτογραφία
            photo_val = row.get('photo_url', None)
            if photo_val and str(photo_val).strip():
                st.markdown("##### 📸 Φωτογραφία Βλάβης")
                try:
                    st.image(photo_val, use_column_width=True)
                except Exception:
                    st.info("Δεν ήταν δυνατή η προεπισκόπηση της φωτογραφίας.")

            # Ιστορικό Ενεργειών (Audit Trail)
            st.markdown("##### 📜 Πλήρες Ιστορικό Ενεργειών & Audit Trail")
            st.text_area("Audit Log History", value=str(row['description']), height=180, disabled=True)

            # Φόρμα Ενημέρωσης
            st.markdown("##### 🔄 Φόρμα Ενημέρωσης & Κλεισίματος Βλάβης")
            with st.form(key=f"update_form_{row['ticket_id']}"):
                u1, u2, u3, u4 = st.columns(4)
                with u1:
                    tech_name = st.text_input("👤 Ονοματεπώνυμο", placeholder="Ονοματεπώνυμο")
                with u2:
                    up_role = st.selectbox("🎭 Ρόλος", ["Security Systems Admin", "Technical Expert", "G4S Security Officer", "Shift Supervisor", "External Contractor"])
                with u3:
                    st_options = ["Open", "Pending", "Closed"]
                    curr_st_idx = st_options.index(row['status']) if row['status'] in st_options else 0
                    up_status = st.selectbox("Κατάσταση", st_options, index=curr_st_idx)
                with u4:
                    up_hours = st.number_input("⏱️ Σύνολο Ωρών (hrs)", min_value=0.0, max_value=200.0, value=float(row.get('resolution_time_hrs', 0.0) or 0.0), step=0.5)

                up_mats = st.text_area("🛠️ Υλικά / Ανταλλακτικά", value=str(row.get('materials_used', '') or ''))
                new_notes = st.text_area("✍️ Προσθήκη Νέων Ενεργειών / Σημειώσεων", placeholder="Γράψτε τι διορθώθηκε...")

                st.markdown("##### 📸 Προσθήκη Φωτογραφίας (Κάμερα ή Αρχείο)")
                u_cam_col, u_file_col = st.columns(2)
                with u_cam_col:
                    up_cam = st.camera_input("📷 Νέα Λήψη από Κάμερα")
                with u_file_col:
                    up_file = st.file_uploader("📁 Νέο Αρχείο Εικόνας", type=["jpg", "jpeg", "png"])

                if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης στη Βάση"):
                    now_str = datetime.now().strftime('%d/%m %H:%M')
                    t_prefix = f" [Χρήστης: {tech_name} ({up_role})]" if tech_name.strip() else ""
                    
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

                    active_up = up_cam if up_cam is not None else up_file
                    if active_up is not None:
                        new_b64 = get_b64_img(active_up)
                        if new_b64:
                            payload["photo_url"] = new_b64

                    try:
                        supabase.table("tickets").update(payload).eq("ticket_id", row['ticket_id']).execute()
                        st.success(f"✅ Η βλάβη {row['ticket_id']} ενημερώθηκε επιτυχώς!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Σφάλμα ενημέρωσης: {e}")

    # ΑΝ ΔΕΝ ΕΧΕΙ ΕΠΙΛΕΓΕΙ ΒΛΑΒΗ -> ΕΜΦΑΝΙΖΕΤΑΙ Η ΛΙΣΤΑ
    else:
        st.subheader("📋 Λίστα Όλων των Βλαβών (Πατήστε σε μια βλάβη για ανάλυση)")
        
        if not df_tickets.empty:
            c_filter, c_search = st.columns([1, 2])
            with c_filter:
                status_filter = st.selectbox("Φιλτράρισμα:", ["Όλες οι Βλάβες", "🔴 Ανοιχτές (Open & Pending)", "🟢 Ολοκληρωμένες (Closed)"])
            with c_search:
                search_txt = st.text_input("🔍 Αναζήτηση:", placeholder="Αναζήτηση κωδικού, περιοχής, συσκευής...")

            display_df = df_tickets.copy()
            if status_filter == "🔴 Ανοιχτές (Open & Pending)":
                display_df = display_df[display_df["status"] != "Closed"]
            elif status_filter == "🟢 Ολοκληρωμένες (Closed)":
                display_df = display_df[display_df["status"] == "Closed"]

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

# ---------------------------------------------------------
# 8. ΟΘΟΝΗ 3 (ΑΡΧΙΚΗ): ΑΝΑΛΥΣΗ ΚΑΤΗΓΟΡΙΩΝ & ΤΜΗΜΑΤΩΝ
# ---------------------------------------------------------
if st.session_state.view_mode == "home" and not df_tickets.empty:
    st.markdown("---")
    st.subheader("📊 Μέσος Χρόνος Αποκατάστασης & Βλάβες ανά Τμήμα")
    
    if "category" in df_tickets.columns:
        cat_summary = df_tickets.groupby("category").agg(
            Σύνολο_Βλαβών=("ticket_id", "count"),
            Σύνολο_Ωρών=("resolution_time_hrs", "sum")
        ).reset_index()
        
        st.dataframe(cat_summary, use_container_width=True, hide_index=True)
