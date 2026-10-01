        import streamlit as st
import pandas as pd
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------------------------------------------------------
# CONFIGURATION & SETUP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Security Ticketing System", layout="wide", page_icon="🛡️️")

DB_TICKETS = "tickets_db.csv"
DB_COMMENTS = "comments_db.csv"
DB_MATERIALS = "materials_db.csv"

# Initialize CSV Databases if they don't exist
if not os.path.exists(DB_TICKETS):
    df_t = pd.DataFrame(columns=[
        "Ticket_ID", "System", "Area_Equipment", "Priority", "Status", 
        "Description", "Date_Reported", "Date_Resolved", "Assigned_To"
    ])
    df_t.to_csv(DB_TICKETS, index=False)

if not os.path.exists(DB_COMMENTS):
    df_c = pd.DataFrame(columns=["Ticket_ID", "Timestamp", "Department", "Author", "Comment"])
    df_c.to_csv(DB_COMMENTS, index=False)

if not os.path.exists(DB_MATERIALS):
    df_m = pd.DataFrame(columns=["Ticket_ID", "Item_Name", "Quantity", "Unit_Cost_EUR", "Total_Cost_EUR", "Order_Status"])
    df_m.to_csv(DB_MATERIALS, index=False)

# Load Data
def load_data():
    return pd.read_csv(DB_TICKETS), pd.read_csv(DB_COMMENTS), pd.read_csv(DB_MATERIALS)

tickets_df, comments_df, materials_df = load_data()

# -----------------------------------------------------------------------------
# HELPER: EMAIL NOTIFICATION
# -----------------------------------------------------------------------------
def send_email_alert(ticket_id, system, area, status, comment=""):
    try:
        sender_email = "notifications@security-system.local"
        receiver_email = "team@security-system.local"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔔 [Security Ticket Alert] {ticket_id} - {system} ({status})"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #002060;">Ενημέρωση Βλάβης: {ticket_id}</h2>
            <p><strong>Σύστημα:</strong> {system} | <strong>Περιοχή:</strong> {area}</p>
            <p><strong>Κατάσταση:</strong> {status}</p>
            <div style="background-color: #f1f5f9; padding: 10px; border-left: 4px solid #0284c7;">
                <strong>Σχόλιο / Ενημέρωση:</strong><br/>{comment}
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))
    except Exception:
        pass

# -----------------------------------------------------------------------------
# HEADER & KPIS
# -----------------------------------------------------------------------------
st.title("🛡️ Security Systems Maintenance Ticketing System")
st.markdown("---")

# Calculate KPIs
total_issues = len(tickets_df)
open_critical = len(tickets_df[(tickets_df["Status"] != "Closed") & (tickets_df["Priority"] == "Critical")])

# MTTR Calculation (in hours)
closed_tickets = tickets_df[tickets_df["Status"] == "Closed"].copy()
if not closed_tickets.empty:
    closed_tickets["Date_Reported"] = pd.to_datetime(closed_tickets["Date_Reported"])
    closed_tickets["Date_Resolved"] = pd.to_datetime(closed_tickets["Date_Resolved"])
    closed_tickets["Downtime"] = (closed_tickets["Date_Resolved"] - closed_tickets["Date_Reported"]).dt.total_seconds() / 3600
    avg_mttr = round(closed_tickets["Downtime"].mean(), 1)
else:
    avg_mttr = 0.0

total_cost = materials_df["Total_Cost_EUR"].sum() if not materials_df.empty else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("TOTAL ISSUES", total_issues)
col2.metric("OPEN / CRITICAL", open_critical, delta_color="inverse")
col3.metric("AVG MTTR (HOURS)", f"{avg_mttr} hrs")
col4.metric("PARTS COST (€)", f"€ {total_cost:,.2f}")

st.markdown("---")

# -----------------------------------------------------------------------------
# SIDEBAR: ΝΕΟ TICKET
# -----------------------------------------------------------------------------
st.sidebar.header("➕ Καταχώρηση Νέας Βλάβης")

sys_cat = st.sidebar.selectbox("Σύστημα", ["CCTV", "Access Control", "Fire Alarm", "Perimeter", "Intercom"])
area_eq = st.sidebar.text_input("Περιοχή / Εξοπλισμός", placeholder="π.χ. Parking / CAM 5 Multi-Lens")
priority = st.sidebar.selectbox("Προτεραιότητα", ["Critical", "High", "Medium", "Low"])

template_text = f"""📌 [ΑΝΑΦΟΡΑ ΒΛΑΒΗΣ ΣΥΣΤΗΜΑΤΩΝ ΑΣΦΑΛΕΙΑΣ]
-------------------------------------------
• Σύστημα: {sys_cat}
• Περιοχή/Εξοπλισμός: {area_eq}
• Περιγραφή Σφάλματος: [Γράψτε εδώ τη βλάβη...]
• Αρχικές Ενέργειες: Έγινε αρχικός έλεγχος τροφοδοσίας / επανεκκίνηση."""

description = st.sidebar.text_area("Περιγραφή Βλάβης", value=template_text, height=180)
uploaded_file = st.sidebar.file_uploader("📷 Φωτογραφία Βλάβης (Προαιρετικό)", type=["jpg", "png", "jpeg"])

if st.sidebar.button("🚀 Υποβολή Ticket"):
    if area_eq:
        new_id = f"INC-{len(tickets_df) + 1:03d}"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        photo_path = ""
        if uploaded_file is not None:
            os.makedirs("uploads", exist_ok=True)
            photo_path = f"uploads/{new_id}_{uploaded_file.name}"
            with open(photo_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        new_ticket = pd.DataFrame([{
            "Ticket_ID": new_id,
            "System": sys_cat,
            "Area_Equipment": area_eq,
            "Priority": priority,
            "Status": "New",
            "Description": description,
            "Date_Reported": now,
            "Date_Resolved": "",
            "Assigned_To": "Unassigned"
        }])
        
        tickets_df = pd.concat([tickets_df, new_ticket], ignore_index=True)
        tickets_df.to_csv(DB_TICKETS, index=False)
        
        st.sidebar.success(f"Το Ticket {new_id} δημιουργήθηκε με επιτυχία!")
        st.rerun()
    else:
        st.sidebar.error("Παρακαλώ συμπληρώστε την Περιοχή/Εξοπλισμός.")

# -----------------------------------------------------------------------------
# MAIN VIEW: ΠΙΝΑΚΑΣ ΒΛΑΒΩΝ & ΕΠΕΞΕΡΓΑΣΙΑ
# -----------------------------------------------------------------------------
st.subheader("📋 Λίστα Βλαβών & Διαχείριση")

if not tickets_df.empty:
    for idx, row in tickets_df.iloc[::-1].iterrows():
        t_id = row["Ticket_ID"]
        status = row["Status"]
        priority_val = row["Priority"]
        
        status_color = "🔴" if status in ["New", "In Progress"] else ("🟡" if status == "Pending Parts" else "🟢")
        
        with st.expander(f"{status_color} **{t_id}** | {row['System']} | {row['Area_Equipment']} | Priority: **{priority_val}** | Status: **{status}**"):
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                st.markdown("**Περιγραφή:**")
                st.text(row["Description"])
                st.caption(f"🕒 Ημερομηνία Αναφοράς: {row['Date_Reported']}")
                
                img_dir = "uploads"
                if os.path.exists(img_dir):
                    for img_file in os.listdir(img_dir):
                        if img_file.startswith(t_id):
                            st.image(os.path.join(img_dir, img_file), caption="Συνημμένη Φωτογραφία", width=300)

            with col_right:
                st.markdown("**🔄 Επεξεργασία & Αλλαγή Κατάστασης**")
                
                stat_options = ["New", "In Progress", "Pending Parts", "Closed"]
                stat_index = stat_options.index(status) if status in stat_options else 0
                new_status = st.selectbox("Status", stat_options, index=stat_index, key=f"stat_{t_id}")
                
                prio_options = ["Critical", "High", "Medium", "Low"]
                prio_index = prio_options.index(priority_val) if priority_val in prio_options else 0
                new_priority = st.selectbox("Priority", prio_options, index=prio_index, key=f"prio_{t_id}")
                
                assigned = st.text_input("Υπεύθυνος (Assigned To)", value=str(row["Assigned_To"]), key=f"ass_{t_id}")
                
                if st.button("💾 Ενημέρωση Ticket", key=f"save_{t_id}"):
                    tickets_df.loc[tickets_df["Ticket_ID"] == t_id, "Status"] = new_status
                    tickets_df.loc[tickets_df["Ticket_ID"] == t_id, "Priority"] = new_priority
                    tickets_df.loc[tickets_df["Ticket_ID"] == t_id, "Assigned_To"] = assigned
                    
                    if new_status == "Closed" and not str(row["Date_Resolved"]):
                        tickets_df.loc[tickets_df["Ticket_ID"] == t_id, "Date_Resolved"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    tickets_df.to_csv(DB_TICKETS, index=False)
                    st.success("Ενημερώθηκε!")
                    st.rerun()

            # -----------------------------------------------------------------
            # TICKET COMMENTS & DISCUSSION THREAD
            # -----------------------------------------------------------------
            st.markdown("---")
            st.markdown("💬 **Ιστορικό Συζήτησης / Σχόλια**")
            
            t_comments = comments_df[comments_df["Ticket_ID"] == t_id]
            for _, c_row in t_comments.iterrows():
                st.info(f"**[{c_row['Timestamp']}] {c_row['Author']} ({c_row['Department']}):**\n{c_row['Comment']}")

            c_col1, c_col2, c_col3 = st.columns([1, 1, 2])
            dept = c_col1.selectbox("Τμήμα", ["Security", "IT", "Technical Dept"], key=f"dept_{t_id}")
            author = c_col2.text_input("Όνομα", value="Security Admin", key=f"auth_{t_id}")
            comment_txt = c_col3.text_input("Νέο Σχόλιο / Απάντηση", key=f"txt_{t_id}")
            
            if st.button("➕ Προσθήκη Σχολίου", key=f"btn_c_{t_id}"):
                if comment_txt:
                    now_c = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_c = pd.DataFrame([{
                        "Ticket_ID": t_id,
                        "Timestamp": now_c,
                        "Department": dept,
                        "Author": author,
                        "Comment": comment_txt
                    }])
                    comments_df = pd.concat([comments_df, new_c], ignore_index=True)
                    comments_df.to_csv(DB_COMMENTS, index=False)
                    st.success("Το σχόλιο καταχωρήθηκε!")
                    st.rerun()

            # -----------------------------------------------------------------
            # MATERIALS & COSTS
            # -----------------------------------------------------------------
            st.markdown("📦 **Υλικά & Κόστος Ανταλλακτικών**")
            t_mats = materials_df[materials_df["Ticket_ID"] == t_id]
            if not t_mats.empty:
                st.dataframe(t_mats[["Item_Name", "Quantity", "Unit_Cost_EUR", "Total_Cost_EUR", "Order_Status"]], use_container_width=True)

            m_col1, m_col2, m_col3, m_col4 = st.columns([2, 1, 1, 1])
            item_name = m_col1.text_input("Όνομα Υλικού", key=f"mname_{t_id}")
            qty = m_col2.number_input("Ποσότητα", min_value=1, value=1, key=f"mqty_{t_id}")
            u_cost = m_col3.number_input("Τιμή Μονάδας (€)", min_value=0.0, value=0.0, key=f"mcost_{t_id}")
            
            if m_col4.button("➕ Προσθήκη Υλικού", key=f"mbtn_{t_id}"):
                if item_name:
                    new_m = pd.DataFrame([{
                        "Ticket_ID": t_id,
                        "Item_Name": item_name,
                        "Quantity": qty,
                        "Unit_Cost_EUR": u_cost,
                        "Total_Cost_EUR": qty * u_cost,
                        "Order_Status": "Requested"
                    }])
                    materials_df = pd.concat([materials_df, new_m], ignore_index=True)
                    materials_df.to_csv(DB_MATERIALS, index=False)
                    st.success("Το υλικό προστέθηκε!")
                    st.rerun()

else:
    st.info("Δεν υπάρχουν καταχωρημένες βλάβες.")


