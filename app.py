import streamlit as st
import pandas as pd
from datetime import datetime
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
# 2. FULL-WIDTH MODERN THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Full Width Container Setup */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
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
        margin-bottom: 20px;
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
        font-size: 0.95rem !important;
        margin-bottom: 4px !important;
    }

    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 16px; 
        border-radius: 12px;
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
        padding: 12px 20px !important;
    }

    /* Expander / Full-Width Card Styling */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
    
    div[data-testid="stForm"] { 
        background-color: #1e293b; 
        border: 1px solid #334155; 
        padding: 24px; 
        border-radius: 14px; 
    }
    
    .full-width-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-left: 5px solid #38bdf8;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DATA RETRIEVAL & METRICS
# ---------------------------------------------------------
try:
    tickets_res = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
    df_tickets = pd.DataFrame(tickets_res.data) if tickets_res.data else pd.DataFrame()
except Exception:
    df_tickets = pd.DataFrame()

HOURLY_RATE = 25.0

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

    if "created_at" in df_tickets.columns:
        df_tickets["created_dt"] = pd.to_datetime(df_tickets["created_at"], errors="coerce")
        df_tickets["updated_dt"] = pd.to_datetime(df_tickets.get("updated_at", df_tickets["created_at"]), errors="coerce")
        
        closed_df = df_tickets[df_tickets["status"] == "Closed"].copy()
        if not closed_df.empty:
            closed_df["duration_days"] = (closed_df["updated_dt"] - closed_df["created_dt"]).dt.total_seconds() / 86400.0
            avg_days_to_close = float(closed_df["duration_days"].mean())

# ---------------------------------------------------------
# 4. HEADER & METRICS BAR
# ---------------------------------------------------------
st.markdown("""
    <div class="pmi-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.2rem; color: #ffffff !important; font-weight: 800;">
                    🛡️ Papastratos (PMI) - Security Systems & Maintenance
                </h1>
                <p style="margin:4px 0 0 0; color: #38bdf8; font-size: 1.05rem; font-weight: 600;">
                    Πλήρης Ανατομία Βλαβών, Υπολογισμός Κόστους, Ωρών & Ιστορικού
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.8); padding: 8px 16px; border-radius: 12px; border: 1px solid #38bdf8;">
                <span style="color: #10b981; font-weight: 800;">● SYSTEM OPERATIONAL</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Σύνολο", total_tck)
k2.metric("🔴 Open", open_tck)
k3.metric("🟡 Pending", pending_tck)
k4.metric("🟢 Closed", closed_tck)
k5.metric("⏱️️ Σύνολο Ωρών", f"{total_hours:.1f}h")
k6.metric("📅 Μ.Ο. Ημερών", f"{avg_days_to_close:.1f}d")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 1. Καταχώρηση Νέας Βλάβης", "📋 2. Αναλυτική Προβολή & Ενημέρωση Βλάβης", "📊 3. Αναλυτικά Σύνολα & KPIs"])

# TAB 1: NEW TICKET FORM (Safe Insert)
with tab1:
    st.subheader("📝 Νέα Αναφορά Βλάβης / Συντήρησης")
    
    with st.form("new_ticket_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tck_id = st.text_input("Κωδικός Ticket", value=f"TCK-{datetime.now().strftime('%m%d-%H%M')}")
            creator_tech = st.text_input("👤 Τεχνικός / Χειριστής Καταχώρησης", placeholder="π.χ. Ανέστης Θεοδωρίδης")
            category = st.selectbox("Καρηγορία Συστήματος", ["CCTV (Κάμερες)", "ACS (Access Control / Τουρνικέ)", "Fire Alarm (Πυρανίχνευση)", "Network / PoE / Fiber", "Άλλο"])
            building_area = st.text_input("Κτίριο / Περιοχή", placeholder="π.χ. BLD8 - Είσοδος Τουρνικέ DR_116")
            device_asset = st.text_input("Συσκευή / Asset ID", placeholder="π.χ. Cam 20 / Reader CR.08L0.01.01")

        with f2:
            priority = st.selectbox("Προτεραιότητα", ["Low", "Medium", "High", "Critical"])
            status = st.selectbox("Αρχική Κατάσταση", ["Open", "Pending", "Closed"])
            duration_hrs = st.number_input("⏱️ Αρχικές Ώρες Εργασίας (hrs)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
            materials = st.text_area("🛠️ Υλικά / Ανταλλακτικά", placeholder="π.χ. 1x PoE Injector, 10m UTP Cat6, 2x RJ45")

        description = st.text_area("Περιγραφή Προβλήματος & Ενεργειών", placeholder="Αναλυτική περιγραφή της βλάβης...")

        if st.form_submit_button("➕ Καταχώρηση Νέας Βλάβης στη Βάση"):
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
            
            try:
                supabase.table("tickets").insert(insert_payload).execute()
                st.success(f"✅ Η βλάβη **{tck_id}** καταχωρήθηκε επιτυχώς!")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Σφάλμα καταχώρησης: {e}")

# TAB 2: FULL-WIDTH TICKET ANALYSIS
with tab2:
    st.subheader("📋 Αναλυτική Προβολή Βλάβης σε Όλη τη Σελίδα (Full-Width)")
    
    if not df_tickets.empty:
        c_filter, c_select = st.columns([1, 2])
        with c_filter:
            status_filter = st.selectbox("Φιλτράρισμα Κατάστασης:", ["Όλες οι Βλάβες", "🔴 Ανοιχτές (Open & Pending)", "🟢 Ολοκληρωμένες (Closed)"])
        
        display_df = df_tickets.copy()
        if status_filter == "🔴 Ανοιχτές (Open & Pending)":
            display_df = display_df[display_df["status"] != "Closed"]
        elif status_filter == "🟢 Ολοκληρωμένες (Closed)":
            display_df = display_df[display_df["status"] == "Closed"]

        if not display_df.empty:
            ticket_options = [f"{row['ticket_id']} | {row['building_area']} | [{row['status']}]" for _, row in display_df.iterrows()]
            selected_option = st.selectbox("🎯 Επιλέξτε Βλάβη για Πλήρη Ανάλυση:", options=ticket_options)
            
            selected_id = selected_option.split(" | ")[0]
            row = display_df[display_df["ticket_id"] == selected_id].iloc[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- ΠΛΗΡΕΣ ΠΛΑΤΟΣ (FULL WIDTH BOX) ---
            badge_color = "#ef4444" if row['status'] == "Open" else ("#f59e0b" if row['status'] == "Pending" else "#10b981")
            
            st.markdown(f"""
            <div class="full-width-box" style="border-left-color: {badge_color};">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <h2 style="margin:0; color:#38bdf8;">📌 {row['ticket_id']} — {row['category']}</h2>
                    <span style="background:{badge_color}; color:#ffffff; padding:6px 16px; border-radius:8px; font-weight:800; font-size:1.1rem;">{row['status']}</span>
                </div>
                <hr style="border-color:#334155; margin:15px 0;">
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    <div><b>📍 Περιοχή / Κτίριο:</b> <br><span style="color:#f8fafc; font-size:1.1rem;">{row['building_area']}</span></div>
                    <div><b>🖥️ Συσκευή / Asset:</b> <br><span style="color:#f8fafc; font-size:1.1rem;">{row['device_asset']}</span></div>
                    <div><b>🚨 Προτεραιότητα:</b> <br><span style="color:#f8fafc; font-size:1.1rem;">{row['priority']}</span></div>
                    <div><b>⏱️ Ώρες Εργασίας:</b> <br><span style="color:#38bdf8; font-size:1.1rem; font-weight:800;">{row.get('resolution_time_hrs', 0.0)} hrs</span></div>
                    <div><b>💰 Εκτιμώμενο Κόστος:</b> <br><span style="color:#10b981; font-size:1.1rem; font-weight:800;">€{(float(row.get('resolution_time_hrs', 0.0) or 0.0) * HOURLY_RATE):,.2f}</span></div>
                </div>
                <hr style="border-color:#334155; margin:15px 0;">
                <div><b>🛠️ Υλικά & Ανταλλακτικά που Χρησιμοποιήθηκαν:</b><br><span style="color:#cbd5e1; font-size:1.05rem;">{row.get('materials_used', 'N/A')}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- ΙΣΤΟΡΙΚΟ ΕΝΕΡΓΕΙΩΝ ΣΕ ΟΛΟ ΤΟ ΠΛΑΤΟΣ ---
            st.markdown("##### 📜 Πλήρες Ιστορικό Ενεργειών & Audit Trail (Full Width)")
            st.text_area("Audit History", value=str(row['description']), height=180, disabled=True)

            # --- ΦΟΡΜΑ ΕΝΗΜΕΡΩΣΗΣ ΣΕ ΟΛΟ ΤΟ ΠΛΑΤΟΣ ---
            st.markdown("##### 🔄 Φόρμα Ενημέρωσης & Κλεισίματος Βλάβης")
            with st.form(key=f"update_form_{row['ticket_id']}"):
                u1, u2, u3 = st.columns(3)
                with u1:
                    tech_name = st.text_input("👤 Τεχνικός / Χειριστής", placeholder="Ονοματεπώνυμο")
                with u2:
                    st_options = ["Open", "Pending", "Closed"]
                    curr_st_idx = st_options.index(row['status']) if row['status'] in st_options else 0
                    up_status = st.selectbox("Κατάσταση", st_options, index=curr_st_idx)
                with u3:
                    up_hours = st.number_input("⏱️ Σύνολο Ωρών Εργασίας (hrs)", min_value=0.0, max_value=200.0, value=float(row.get('resolution_time_hrs', 0.0) or 0.0), step=0.5)

                up_mats = st.text_area("🛠️ Υλικά / Ανταλλακτικά", value=str(row.get('materials_used', '') or ''))
                new_notes = st.text_area("✍️️ Προσθήκη Νέων Ενεργειών / Σημειώσεων", placeholder="Γράψτε τι διορθώθηκε...")

                if st.form_submit_button("💾 Αποθήκευση Ενημέρωσης στη Βάση"):
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

                    supabase.table("tickets").update(payload).eq("ticket_id", row['ticket_id']).execute()
                    st.success(f"✅ Η βλάβη {row['ticket_id']} ενημερώθηκε επιτυχώς!")
                    st.rerun()
        else:
            st.info("Δεν βρέθηκαν βλάβες για το επιλεγμένο φίλτρο.")
    else:
        st.info("Δεν υπάρχουν καταχωρημένες βλάβες στη βάση.")

# TAB 3: FULL ANALYTICS
with tab3:
    st.subheader("📊 Αναλυτικά Σύνολα, Κόστη & KPIs")
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
