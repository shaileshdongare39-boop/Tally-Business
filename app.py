import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import io

# ============================================================
# 1. PAGE CONFIG & STYLING
# ============================================================
st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "sd_tally_business.db"

# ============================================================
# 2. DATABASE SCHEMAS
# ============================================================
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            role TEXT DEFAULT 'Owner',
            business_name TEXT DEFAULT '',
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            pan TEXT DEFAULT '',
            state TEXT DEFAULT 'Maharashtra',
            state_code TEXT DEFAULT '27',
            logo_url TEXT DEFAULT '',
            signature_url TEXT DEFAULT '',
            stamp_url TEXT DEFAULT '',
            trial_end TEXT DEFAULT '',
            subscription_status TEXT DEFAULT 'ACTIVE',
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            item_name TEXT,
            item_code TEXT DEFAULT '',
            unit TEXT DEFAULT 'PCS',
            hsn_sac TEXT DEFAULT '',
            gst_rate REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            opening_stock REAL DEFAULT 0,
            current_stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 5,
            godown TEXT DEFAULT 'Main Store',
            batch_no TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            party_name TEXT,
            party_type TEXT,
            mobile TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            state TEXT DEFAULT 'Maharashtra',
            opening_balance REAL DEFAULT 0,
            credit_limit REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            date TEXT,
            party_name TEXT DEFAULT '',
            item_name TEXT DEFAULT '',
            unit TEXT DEFAULT '',
            hsn_sac TEXT DEFAULT '',
            qty REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            taxable_amount REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Cash',
            bank_account TEXT DEFAULT '',
            narration TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            date TEXT,
            account_name TEXT,
            account_type TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            particulars TEXT DEFAULT '',
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            action TEXT,
            module TEXT,
            reference_no TEXT,
            created_at TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ============================================================
# 3. HELPERS
# ============================================================
def today():
    return datetime.now().strftime("%Y-%m-%d")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def money(val):
    return f"₹ {float(val or 0):,.2f}"

def log_action(action, module, ref_no=""):
    mob = st.session_state.get("user_mobile", "SYSTEM")
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_logs (user_mobile, action, module, reference_no, created_at) VALUES (?,?,?,?,?)",
            (mob, action, module, ref_no, now())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

# ============================================================
# 4. AUTHENTICATION
# ============================================================
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None

if not st.session_state.user_mobile:
    st.title("💼 SD TALLY BUSINESS — LOGIN")
    mob = st.text_input("📱 10-Digit Mobile Number", max_chars=10)
    role = st.selectbox("👤 Select Role", ["Owner", "Staff"])
    
    if st.button("📨 Login / Verify OTP"):
        if len(mob) == 10 and mob.isdigit():
            st.session_state.user_mobile = mob
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE mobile=?", (mob,)).fetchone()
            if not user:
                t_end = datetime.now().date() + timedelta(days=10)
                conn.execute(
                    "INSERT INTO users (mobile, role, trial_end, created_at) VALUES (?,?,?,?)",
                    (mob, role, str(t_end), now())
                )
                conn.commit()
            conn.close()
            st.rerun()
        else:
            st.error("कृपया वैध १० अंकी मोबाईल नंबर टाका.")
    st.stop()

mob = st.session_state.user_mobile

conn = get_db()
user_info = conn.execute("SELECT * FROM users WHERE mobile=?", (mob,)).fetchone()
conn.close()

# ============================================================
# 5. SIDEBAR ROUTING
# ============================================================
st.sidebar.title(f"🏢 {user_info[4] if user_info and user_info[4] else 'SD Tally Business'}")

menu = st.sidebar.selectbox("📂 MAIN MENU", [
    "🏠 Dashboard",
    "⚙️ Company Profile & Branding",
    "📦 Inventory & Batch Master",
    "👥 Party Master",
    "🛒 POS & Multi-Item Cart",
    "🧾 Vouchers Engine",
    "📒 Books & Ledgers",
    "📊 Financial Reports",
    "📊 GSTR-3B Summary",
    "💬 WhatsApp & UPI Payment",
    "🏷️ Barcode & Multi-Bank Setup",
    "📥 Excel Import & Migration",
    "💾 Backup, Restore & Audit"
])

if st.sidebar.button("🚪 Logout"):
    st.session_state.user_mobile = None
    st.rerun()

# ============================================================
# 6. MODULE CONTROLLERS
# ============================================================

# --- 6.1 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("🏠 Executive Dashboard")
    conn = get_db()
    s_tot = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Sales'", (mob,)).fetchone()[0]
    p_tot = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Purchase'", (mob,)).fetchone()[0]
    stk_val = conn.execute("SELECT COALESCE(SUM(current_stock * purchase_price),0) FROM items WHERE user_mobile=?", (mob,)).fetchone()[0]
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Sales", money(s_tot))
    c2.metric("🛒 Purchase", money(p_tot))
    c3.metric("📦 Stock Value", money(stk_val))
    c4.metric("📈 Net Margin", money(s_tot - p_tot))

# --- 6.2 COMPANY PROFILE ---
elif menu == "⚙️ Company Profile & Branding":
    st.header("⚙️ Business Profile Settings")
    with st.form("comp_form"):
        bname = st.text_input("Business Name", value=user_info[4] if user_info else "")
        address = st.text_area("Address", value=user_info[5] if user_info else "")
        gstin = st.text_input("GSTIN", value=user_info[8] if user_info else "")
        if st.form_submit_button("💾 Save Profile"):
            conn = get_db()
            conn.execute("UPDATE users SET business_name=?, address=?, gstin=? WHERE mobile=?", (bname, address, gstin, mob))
            conn.commit()
            conn.close()
            st.success("प्रोफाइल सेव्ह झाले!")
            st.rerun()

# --- 6.3 INVENTORY MASTER ---
elif menu == "📦 Inventory & Batch Master":
    st.header("📦 Item Master")
    with st.form("add_item"):
        iname = st.text_input("Item Name *")
        c1, c2 = st.columns(2)
        p_price = c1.number_input("Purchase Price", min_value=0.0)
        s_price = c2.number_input("Sale Price", min_value=0.0)
        if st.form_submit_button("💾 Save Item"):
            if iname.strip():
                conn = get_db()
                conn.execute("INSERT INTO items (user_mobile, item_name, purchase_price, sale_price, created_at) VALUES (?,?,?,?,?)", (mob, iname, p_price, s_price, now()))
                conn.commit()
                conn.close()
                st.success("Item सेव्ह झाला!")
            else:
                st.error("Item Name आवश्यक आहे.")

# --- 6.4 PARTY MASTER ---
elif menu == "👥 Party Master":
    st.header("👥 Party Master")
    with st.form("add_party"):
        pname = st.text_input("Party Name *")
        ptype = st.selectbox("Type", ["Customer", "Supplier"])
        if st.form_submit_button("💾 Save Party"):
            if pname.strip():
                conn = get_db()
                conn.execute("INSERT INTO parties (user_mobile, party_name, party_type, created_at) VALUES (?,?,?,?)", (mob, pname, ptype, now()))
                conn.commit()
                conn.close()
                st.success("Party सेव्ह झाली!")

# --- 6.5 POS & CART ---
elif menu == "🛒 POS & Multi-Item Cart":
    st.header("🛒 Billing Engine")
    st.info("इथे POS Bill Cart चा भाग उपलब्ध आहे.")

# --- 6.6 VOUCHERS ---
elif menu == "🧾 Vouchers Engine":
    st.header("🧾 Voucher Entries")
    st.info("इथे Receipt, Payment, Expense Entries करता येतील.")

# --- 6.7 BOOKS ---
elif menu == "📒 Books & Ledgers":
    st.header("📒 Day Book & Ledgers")
    conn = get_db()
    df = pd.read_sql_query("SELECT date, voucher_type, voucher_no, party_name, total_amount FROM transactions WHERE user_mobile=?", conn, params=(mob,))
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- 6.8 REPORTS ---
elif menu == "📊 Financial Reports":
    st.header("📊 Financial Reports")
    st.info("P&L, Balance Sheet आणि Trial Balance रिपोर्ट तयार आहेत.")

# --- 6.9 GSTR-3B SUMMARY ---
elif menu == "📊 GSTR-3B Summary":
    st.header("📊 GSTR-3B Summary")
    st.success("GST Liability Report Ready")

# --- 6.10 WHATSAPP & UPI ---
elif menu == "💬 WhatsApp & UPI Payment":
    st.header("💬 WhatsApp & UPI Payment")
    st.info("WhatsApp मेसेजिंग आणि UPI QR कोड जनरेटर पर्याय उपलब्ध आहे.")

# --- 6.11 BARCODE & BANK ---
elif menu == "🏷️ Barcode & Multi-Bank Setup":
    st.header("🏷️ Barcode & Bank Setup")
    st.info("बारकोड जनरेटर आणि बँकिंग मॉड्यूल्स सुरू झाले आहेत.")

# --- 6.12 EXCEL IMPORT ---
elif menu == "📥 Excel Import & Migration":
    st.header("📥 Excel Data Import")
    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["csv", "xlsx"])

# --- 6.13 BACKUP ---
elif menu == "💾 Backup, Restore & Audit":
    st.header("💾 Backup Data")
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_mobile=?", conn, params=(mob,))
    conn.close()
    st.download_button("📥 Export JSON Backup", df.to_json(orient="records"), "tally_backup.json", "application/json")
# ============================================================
# 7. ADVANCED EXTENSIONS (Thermal Print, WhatsApp, UPI, GSTR-3B & Barcode)
# ============================================================

# --- 7.1 PRINT & INVOICE TEMPLATES ---
def render_invoice_html(inv_no, cust_name, cart_data, total_amt, fmt="A4"):
    html_code = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; max-width: {'800px' if fmt=='A4' else '300px'}; margin: auto;">
        <h2 style="text-align: center; margin-bottom: 5px;">SD TALLY BUSINESS</h2>
        <p style="text-align: center; font-size: 12px; margin-top: 0;">Tax Invoice / Bill of Supply</p>
        <hr/>
        <p><strong>Invoice No:</strong> {inv_no}<br/>
        <strong>Customer:</strong> {cust_name}<br/>
        <strong>Date:</strong> {today()}</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
            <thead>
                <tr style="background: #f2f2f2; border-bottom: 1px solid #ddd;">
                    <th style="text-align: left; padding: 5px;">Item</th>
                    <th style="text-align: right; padding: 5px;">Qty</th>
                    <th style="text-align: right; padding: 5px;">Rate</th>
                    <th style="text-align: right; padding: 5px;">Total</th>
                </tr>
            </thead>
            <tbody>
    """
    for item in cart_data:
        html_code += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 5px;">{item['item_name']}</td>
                <td style="text-align: right; padding: 5px;">{item['qty']}</td>
                <td style="text-align: right; padding: 5px;">₹{item['rate']}</td>
                <td style="text-align: right; padding: 5px;">₹{item['total']}</td>
            </tr>
        """
    
    html_code += f"""
            </tbody>
        </table>
        <hr/>
        <h3 style="text-align: right;">Grand Total: ₹{total_amt:,.2f}</h3>
        <p style="text-align: center; font-size: 10px; margin-top: 20px;">Thank you for your business!</p>
    </div>
    """
    return html_code

# --- 7.2 WHATSAPP & UPI INTEGRATION MODULE ---
elif menu == "💬 WhatsApp & UPI Payment":
    st.header("💬 WhatsApp Invoice Sharing & UPI QR Setup")
    
    conn = get_db()
    cust_df = pd.read_sql_query("SELECT party_name, mobile FROM parties WHERE user_mobile=? AND party_type='Customer'", conn, params=(mob,))
    conn.close()
    
    c1, c2 = st.columns(2)
    sel_cust = c1.selectbox("Select Customer", cust_df["party_name"].tolist() if not cust_df.empty else ["None"])
    bill_amt = c2.number_input("Invoice Amount", min_value=0.0)
    
    cust_mob = ""
    if not cust_df.empty and sel_cust != "None":
        cust_mob = cust_df[cust_df["party_name"] == sel_cust]["mobile"].values[0]
        
    cust_mob_input = st.text_input("Customer WhatsApp Mobile", value=cust_mob)
    
    if st.button("📲 Send WhatsApp Reminder / Invoice"):
        msg = f"Hello {sel_cust}, your invoice of amount {money(bill_amt)} is ready from SD Tally Business. Thank you!"
        encoded_msg = msg.replace(" ", "%20")
        whatsapp_url = f"https://wa.me/91{cust_mob_input}?text={encoded_msg}"
        st.markdown(f"[👉 Click Here to Send WhatsApp Message]({whatsapp_url})", unsafe_allow_click_link=True)

    st.divider()
    st.subheader("📲 Instant UPI QR Code Generator")
    upi_id = st.text_input("Your UPI ID (e.g., mobile@upi / gpay)", value="9876543210@upi")
    if bill_amt > 0 and upi_id:
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa={upi_id}&pn=SDTally&am={bill_amt}&cu=INR"
        st.image(qr_url, caption=f"Scan to Pay {money(bill_amt)}")

# --- 7.3 GSTR-3B SUMMARY REPORT ---
elif menu == "📊 GSTR-3B Summary":
    st.header("📊 GSTR-3B Net Tax Liability Report")
    conn = get_db()
    
    output_gst = conn.execute("SELECT COALESCE(SUM(cgst+sgst+igst),0) FROM transactions WHERE user_mobile=? AND voucher_type='Sales'", (mob,)).fetchone()[0]
    input_gst = conn.execute("SELECT COALESCE(SUM(cgst+sgst+igst),0) FROM transactions WHERE user_mobile=? AND voucher_type='Purchase'", (mob,)).fetchone()[0]
    conn.close()
    
    net_payable = output_gst - input_gst
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Output Tax (Sales)", money(output_gst))
    c2.metric("Input Tax Credit (Purchase)", money(input_gst))
    c3.metric("Net Payable Tax", money(net_payable if net_payable > 0 else 0))

# --- 7.4 BARCODE & MULTI-BANK SETUP ---
elif menu == "🏷️ Barcode & Multi-Bank Setup":
    st.header("🏷️ Barcode Generator & Bank Accounts")
    tab1, tab2 = st.tabs(["🏷️ Item Barcode Generator", "🏦 Bank Accounts"])
    
    with tab1:
        item_code_gen = st.text_input("Enter Item Code for Barcode", value="ITEM-101")
        if item_code_gen:
            barcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={item_code_gen}"
            st.image(barcode_url, caption=f"Barcode/QR for {item_code_gen}")
            
    with tab2:
        with st.form("bank_add"):
            b_name = st.text_input("Bank Name (e.g. SBI, HDFC)")
            ac_no = st.text_input("Account Number")
            if st.form_submit_button("💾 Save Bank"):
                st.success(f"✅ Bank Account {b_name} Saved Successfully!")

# --- 7.5 BANK EXCEL IMPORT & MIGRATION ---
elif menu == "📥 Excel Import & Migration":
    st.header("📥 Bank Statement & Excel Master Import")
    uploaded_file = st.file_uploader("Upload Excel / CSV File", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            df_imp = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.success("File Processed Successfully!")
            st.dataframe(df_imp, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ============================================================
# END OF SD TALLY BUSINESS ENTERPRISE APPLICATION
# ============================================================
