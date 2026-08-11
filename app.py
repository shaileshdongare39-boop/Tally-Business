import streamlit as st
import pandas as pd
import sqlite3
import random
import io
from datetime import datetime, timedelta

try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None

# 1. Page Config & Dark Styling (Same as your Screenshot)
st.set_page_config(
    page_title="SD TALLY BUSINESS",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Custom Dark CSS (Matching Screenshots)
st.markdown("""
    <style>
    .stApp { background-color: #1e1e28; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #252533; }
    .main-header {
        background-color: #2b2b3d; color: #ffffff;
        padding: 20px; border-radius: 10px; margin-bottom: 20px;
        border-left: 5px solid #38bdf8;
    }
    .main-header h1 { color: #ffffff; font-size: 2rem; font-weight: 700; margin: 0; }
    .account-card {
        background-color: #2b384e; padding: 12px 16px; border-radius: 8px;
        margin-bottom: 15px; border-left: 4px solid #38bdf8;
    }
    .plan-card {
        background-color: #253346; padding: 12px 16px; border-radius: 8px;
        color: #38bdf8; margin-bottom: 20px;
    }
    .stMetric {
        background-color: #2b2b3d; padding: 15px; border-radius: 8px;
        border-left: 4px solid #0284c7; color: white;
    }
    .stButton>button {
        background-color: #0284c7; color: white; border-radius: 6px;
        height: 45px; font-weight: bold; border: none; width: 100%;
    }
    .thermal-receipt {
        background-color: #ffffff; color: #000000; padding: 15px; border: 1px dashed #000;
        font-family: 'Courier New', Courier, monospace; width: 280px; margin: auto;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Database Initialization
DB_FILE = "sd_tally_v3_master.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    mobile TEXT PRIMARY KEY,
                    name TEXT,
                    reg_date TEXT,
                    trial_end_date TEXT,
                    is_paid INTEGER DEFAULT 0,
                    paid_till TEXT,
                    role TEXT DEFAULT 'Owner'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT UNIQUE,
                    barcode TEXT,
                    hsn_sac TEXT,
                    godown TEXT,
                    batch_no TEXT,
                    expiry_date TEXT,
                    sale_price REAL,
                    purchase_price REAL,
                    gst_rate REAL,
                    stock_qty REAL,
                    min_stock_alert REAL DEFAULT 5
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT UNIQUE,
                    gstin TEXT,
                    mobile TEXT,
                    party_type TEXT,
                    opening_balance REAL DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voucher_type TEXT,
                    voucher_no TEXT,
                    date TEXT,
                    party_name TEXT,
                    item_name TEXT,
                    hsn_sac TEXT,
                    qty REAL,
                    rate REAL,
                    taxable_amt REAL,
                    gst_rate REAL,
                    cgst REAL,
                    sgst REAL,
                    igst REAL,
                    total_amt REAL,
                    payment_mode TEXT,
                    eway_bill_no TEXT,
                    irn_no TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS capital_bank_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    account_type TEXT,
                    particulars TEXT,
                    amount REAL,
                    txn_type TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# 3. Session State Setup
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "Owner"
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

def check_subscription(mobile):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT reg_date, trial_end_date, is_paid, paid_till, role FROM users WHERE mobile=?", (mobile,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return "NEW_USER"
    
    st.session_state.user_role = user[4] if len(user) > 4 and user[4] else "Owner"
    today = datetime.now().date()
    trial_end = datetime.strptime(user[1], "%Y-%m-%d").date()
    
    if user[2] == 1 and user[3]:
        paid_till = datetime.strptime(user[3], "%Y-%m-%d").date()
        if today <= paid_till:
            return "ACTIVE_PRO"
    
    if today <= trial_end:
        days_left = (trial_end - today).days
        return f"FREE_TRIAL ({days_left} days left)"
    
    return "EXPIRED"

# 4. LOGIN / AUTHENTICATION
if not st.session_state.user_mobile:
    st.markdown("""
        <div class="main-header">
            <h1>🏢 SD TALLY BUSINESS</h1>
            <p>Cloud Business ERP & Enterprise Accounting Suite</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, _ = st.columns([1, 1])
    with col1:
        st.subheader("🔑 Login to Workspace")
        mobile = st.text_input("📱 Mobile Number", max_chars=10, placeholder="Enter 10-digit mobile number")
        
        if not st.session_state.otp_sent:
            if st.button("Send Verification OTP"):
                if len(mobile) == 10 and mobile.isdigit():
                    st.session_state.generated_otp = str(random.randint(1000, 9999))
                    st.session_state.otp_sent = True
                    st.info(f"🔑 Testing OTP: **{st.session_state.generated_otp}**")
                else:
                    st.error("Please enter a valid 10-digit mobile number.")
        else:
            otp_in = st.text_input("🔑 Enter 4-Digit OTP")
            role_sel = st.selectbox("Select Access Role", ["Owner", "Salesman / Staff"])
            if st.button("Verify OTP & Login"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.user_mobile = mobile
                    st.session_state.user_role = role_sel
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("SELECT mobile FROM users WHERE mobile=?", (mobile,))
                    if not c.fetchone():
                        today = datetime.now().date()
                        trial_end = today + timedelta(days=10)
                        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, 0, NULL, ?)",
                                  (mobile, "Business User", str(today), str(trial_end), role_sel))
                        conn.commit()
                    conn.close()
                    st.rerun()
                else:
                    st.error("Invalid OTP entered.")
    st.stop()

# 5. SIDEBAR (Matching Screenshots Style)
sub_status = check_subscription(st.session_state.user_mobile)

st.sidebar.markdown(f"""
    <div class="account-card">
        👤 <b>Account:</b> <span style="color:#4ade80;">{st.session_state.user_mobile}</span>
    </div>
    <div class="plan-card">
        🎁 <b>Plan:</b> {sub_status}
    </div>
    <div style="margin-bottom:15px;">
        <h3 style="margin:0; color:#ffffff;">🏢 SD TALLY BUSINESS</h3>
    </div>
""", unsafe_allow_html=True)

# Navigation Menu Logic
if st.session_state.user_role == "Salesman / Staff":
    menu_options = ["Tax Invoice (Sales)", "Barcode Quick Billing", "Thermal Receipt Print"]
else:
    menu_options = [
        "Dashboard",
        "Tax Invoice (Sales)",
        "Barcode Quick Billing",
        "Thermal Receipt Print",
        "Purchase & GSTR-2B Import",
        "All Tally Vouchers (F4-F9)",
        "Capital & Bank Account Management",
        "Bank Statement Excel Import",
        "Masters (Items HSN & Parties)",
        "Receivables & Payment Reminders",
        "GST Reports (GSTR-1, 2B & 3B)",
        "e-Way Bill & e-Invoicing Portal",
        "Profit & Loss Account",
        "Balance Sheet",
        "Company Branding & Signature",
        "Automated Cloud Backup",
        "Account & Billing"
    ]

menu = st.sidebar.radio("Enterprise Navigation", menu_options)

st.markdown("""
    <div class="main-header">
        <h1>SD TALLY BUSINESS</h1>
        <p>Complete Enterprise Accounting & GST Management</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------- MODULES ----------------------------

# 1. DASHBOARD
if menu == "Dashboard":
    st.subheader("📊 Executive Business Analytics")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice')", conn)
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase'", conn)
    bank_df = pd.read_sql_query("SELECT SUM(amount) as total FROM capital_bank_ledger WHERE account_type='Bank Account'", conn)
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    total_bank = bank_df['total'].iloc[0] or 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchases", f"₹ {total_pur:,.2f}")
    c3.metric("Net Profit", f"₹ {(total_sales - total_pur):,.2f}")
    c4.metric("Bank Balance", f"₹ {total_bank:,.2f}")

# 2. TAX INVOICE (SALES)
elif menu == "Tax Invoice (Sales)":
    st.subheader("🧾 Create Tax Invoice")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Invoice Number", f"INV-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    selected_party = c3.selectbox("Customer Name", parties_list) if parties_list else c3.text_input("Customer Name")
    
    if items_list:
        selected_item = st.selectbox("Select Product", items_list)
        c = conn.cursor()
        c.execute("SELECT hsn_sac, sale_price, gst_rate, stock_qty FROM inventory WHERE item_name=?", (selected_item,))
        item_data = c.fetchone()
        hsn_sac, default_rate, default_gst, curr_stock = item_data[0], item_data[1], item_data[2], item_data[3]
    else:
        selected_item = st.text_input("Product Name")
        hsn_sac = st.text_input("HSN Code", "9983")
        default_rate, default_gst = 100.0, 18.0

    cq, cr, cg, cp = st.columns(4)
    qty = cq.number_input("Quantity", min_value=0.1, value=1.0)
    rate = cr.number_input("Rate per Unit (₹)", min_value=0.0, value=float(default_rate))
    gst_rate = cg.number_input("GST Rate (%)", value=float(default_gst))
    pay_mode = cp.selectbox("Payment Mode", ["Bank / UPI", "Cash", "Credit (Pending)"])

    taxable = qty * rate
    cgst = (taxable * (gst_rate / 2)) / 100
    sgst = (taxable * (gst_rate / 2)) / 100
    grand_total = taxable + cgst + sgst

    if st.button("Save & Post Tax Invoice"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("Tax Invoice", v_no, str(v_date), selected_party, selected_item, hsn_sac, qty, rate, taxable, gst_rate, cgst, sgst, 0.0, grand_total, pay_mode))
        c.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ?", (qty, selected_item))
        conn.commit()
        st.success(f"✅ Tax Invoice {v_no} Saved Successfully!")
        
        wa_text = f"SD TALLY BUSINESS Invoice {v_no}%0AParty: {selected_party}%0ATotal: Rs.{grand_total:.2f}%0APay via UPI: 8381085702@ibl"
        st.markdown(f"[📲 **Send Invoice via WhatsApp**](https://wa.me/?text={wa_text})")

# 3. BARCODE QUICK BILLING
elif menu == "Barcode Quick Billing":
    st.subheader("⚡ Barcode Camera Billing Scanner")
    barcode_input = st.text_input("🔍 Scan Barcode ID", placeholder="Click & Scan Barcode...")
    if barcode_input:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT item_name, sale_price, gst_rate, stock_qty FROM inventory WHERE barcode=?", (barcode_input,))
        item = c.fetchone()
        if item:
            st.success(f"Item Found: **{item[0]}** | Selling Price: ₹{item[1]} | Stock: {item[3]}")
        else:
            st.error("Item barcode not found.")

# 4. THERMAL RECEIPT PRINT
elif menu == "Thermal Receipt Print":
    st.subheader("🖨️ POS Thermal Printer Receipt Generator")
    conn = get_db()
    vouchers = pd.read_sql_query("SELECT voucher_no, party_name, date, total_amt FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice')", conn)
    if not vouchers.empty:
        selected_v = st.selectbox("Select Invoice", vouchers['voucher_no'].tolist())
        v_details = vouchers[vouchers['voucher_no'] == selected_v].iloc[0]
        
        receipt_html = f"""
        <div class="thermal-receipt">
            <center>
                <h3><b>SD TALLY BUSINESS</b></h3>
                <p>Tax Invoice Receipt</p>
                <p>--------------------------------</p>
            </center>
            <p>Invoice No: {v_details['voucher_no']}</p>
            <p>Date: {v_details['date']}</p>
            <p>Customer: {v_details['party_name']}</p>
            <p>--------------------------------</p>
            <p><b>TOTAL PAID: Rs. {v_details['total_amt']:.2f}</b></p>
            <p>--------------------------------</p>
        </div>
        """
        st.markdown(receipt_html, unsafe_allow_html=True)
        st.button("🖨️ Print Receipt")

# 5. PURCHASE ENTRY & GSTR-2B
elif menu == "Purchase & GSTR-2B Import":
    st.subheader("🛒 Purchase Entry & GSTR-2B Import")
    tab1, tab2 = st.tabs(["📝 New Purchase Entry", "📥 GSTR-2B ITC Matching"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        parties_list = [row[0] for row in c.execute("SELECT party_name FROM parties WHERE party_type='Supplier'").fetchall()]
        items_list = [row[0] for row in c.execute("SELECT item_name FROM inventory").fetchall()]
        
        c1, c2, c3 = st.columns(3)
        v_no = c1.text_input("Purchase Bill No", f"PUR-{random.randint(1000,9999)}")
        v_date = c2.date_input("Date", datetime.now())
        selected_party = c3.selectbox("Supplier Name", parties_list) if parties_list else c3.text_input("Supplier Name")
        
        selected_item = st.selectbox("Product Name", items_list) if items_list else st.text_input("Product Name")
        hsn = st.text_input("HSN Code", "9983")
        
        cq, cr, cg = st.columns(3)
        qty = cq.number_input("Qty Received", min_value=0.1, value=1.0)
        rate = cr.number_input("Purchase Rate", min_value=0.0, value=100.0)
        gst_rate = cg.number_input("GST %", value=18.0)

        taxable = qty * rate
        tax_amt = (taxable * gst_rate) / 100
        grand_total = taxable + tax_amt

        if st.button("Save Purchase & Update Stock"):
            c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      ("Purchase", v_no, str(v_date), selected_party, selected_item, hsn, qty, rate, taxable, gst_rate, tax_amt/2, tax_amt/2, 0.0, grand_total, "Credit"))
            c.execute("UPDATE inventory SET stock_qty = stock_qty + ? WHERE item_name = ?", (qty, selected_item))
            conn.commit()
            st.success("✅ Purchase Saved & Stock Increased!")

    with tab2:
        st.file_uploader("Upload GSTR-2B File (Excel/CSV)", type=["csv", "xlsx"])

# 6. ALL TALLY VOUCHERS
elif menu == "All Tally Vouchers (F4-F9)":
    st.subheader("📑 Tally Vouchers Entry")
    v_type = st.selectbox("Select Voucher Type", ["Receipt (F6)", "Payment (F5)", "Contra (F4)", "Journal (F7)", "Credit Note", "Debit Note"])
    
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Voucher No", f"{v_type[:3].upper()}-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    party = c3.selectbox("Ledger Account", parties_list) if parties_list else c3.text_input("Ledger Account")
    
    amt = st.number_input("Transaction Amount (₹)", min_value=1.0)
    narration = st.text_area("Narration / Entry Particulars")
    
    if st.button("Post Voucher Entry"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, '9983', 0, 0, ?, 0, 0, 0, 0, ?, ?)""",
                  (v_type, v_no, str(v_date), party, narration, amt, amt, "Bank/Cash"))
        conn.commit()
        st.success(f"✅ {v_type} Entry Posted!")

# 7. CAPITAL & BANK MANAGEMENT
elif menu == "Capital & Bank Account Management":
    st.subheader("🏦 Capital & Bank Ledger Management")
    conn = get_db()
    c = conn.cursor()
    tab1, tab2 = st.tabs(["💰 Capital Account", "🏛️ Bank Account Ledger"])
    
    with tab1:
        cap_amt = st.number_input("Capital Amount (₹)", min_value=1.0)
        cap_type = st.selectbox("Type", ["CAPITAL_DEPOSIT", "DRAWINGS"])
        if st.button("Post Capital Entry"):
            c.execute("INSERT INTO capital_bank_ledger (date, account_type, particulars, amount, txn_type) VALUES (?, 'Capital Account', 'Capital Entry', ?, ?)",
                      (str(datetime.now().date()), cap_amt, cap_type))
            conn.commit()
            st.success("Capital Entry Posted!")
            
    with tab2:
        bank_amt = st.number_input("Bank Amount (₹)", min_value=1.0)
        b_type = st.radio("Txn Type", ["DEPOSIT", "WITHDRAWAL"])
        if st.button("Post Bank Entry"):
            c.execute("INSERT INTO capital_bank_ledger (date, account_type, particulars, amount, txn_type) VALUES (?, 'Bank Account', 'Bank Ledger Entry', ?, ?)",
                      (str(datetime.now().date()), bank_amt, b_type))
            conn.commit()
            st.success("Bank Entry Saved!")

# 8. BANK STATEMENT EXCEL IMPORT
elif menu == "Bank Statement Excel Import":
    st.subheader("📂 Import Bank Statement (Excel/CSV)")
    st.file_uploader("Choose Statement File", type=["xlsx", "csv"])

# 9. MASTERS
elif menu == "Masters (Items HSN & Parties)":
    st.subheader("⚙️ Master Configuration")
    tab1, tab2 = st.tabs(["📦 Stock Item Master", "👤 Ledger Party Master"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        i_name = st.text_input("Item Name")
        b_code = st.text_input("Barcode ID", value="89012345")
        s_price = st.number_input("Selling Price", value=100.0)
        p_price = st.number_input("Purchase Price", value=80.0)
        op_stock = st.number_input("Opening Stock", value=10.0)
        if st.button("Save Item Master"):
            c.execute("INSERT INTO inventory (item_name, barcode, hsn_sac, godown, batch_no, expiry_date, sale_price, purchase_price, gst_rate, stock_qty, min_stock_alert) VALUES (?, ?, '9983', 'Main', 'B1', '2026-12-31', ?, ?, 18.0, ?, 5.0)", (i_name, b_code, s_price, p_price, op_stock))
            conn.commit()
            st.success("Item Master Saved!")
            
    with tab2:
        p_name = st.text_input("Party Name")
        p_type = st.selectbox("Party Type", ["Customer", "Supplier"])
        if st.button("Save Party Master"):
            c.execute("INSERT INTO parties (party_name, gstin, mobile, party_type, opening_balance) VALUES (?, 'NA', 'NA', ?, 0.0)", (p_name, p_type))
            conn.commit()
            st.success("Party Master Saved!")

# 10. RECEIVABLES & REMINDERS
elif menu == "Receivables & Payment Reminders":
    st.subheader("📒 Outstanding Receivables")
    conn = get_db()
    df = pd.read_sql_query("SELECT party_name, SUM(total_amt) as pending FROM vouchers WHERE payment_mode='Credit (Pending)' GROUP BY party_name", conn)
    st.dataframe(df, use_container_width=True)

# 11. GST REPORTS
elif menu == "GST Reports (GSTR-1, 2B & 3B)":
    st.subheader("📑 Statutory GST Reports Hub")
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM vouchers", conn)
    st.dataframe(df, use_container_width=True)

# 12. E-WAY BILL
elif menu == "e-Way Bill & e-Invoicing Portal":
    st.subheader("🚚 Government e-Way Bill & e-Invoicing")
    conn = get_db()
    vouchers = pd.read_sql_query("SELECT voucher_no, party_name, total_amt FROM vouchers WHERE total_amt >= 50000", conn)
    st.dataframe(vouchers, use_container_width=True)

# 13. PROFIT & LOSS
elif menu == "Profit & Loss Account":
    st.subheader("📊 Profit & Loss Account")
    conn = get_db()
    sales = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice')", conn).iloc[0, 0] or 0.0
    purchases = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Purchase'", conn).iloc[0, 0] or 0.0
    st.metric("Net Revenue Operating Profit", f"₹ {(sales - purchases):,.2f}")

# 14. BALANCE SHEET
elif menu == "Balance Sheet":
    st.subheader("⚖️ Balance Sheet")
    conn = get_db()
    stock_val = pd.read_sql_query("SELECT SUM(stock_qty * purchase_price) FROM inventory", conn).iloc[0, 0] or 0.0
    st.metric("Total Closing Assets Stock Value", f"₹ {stock_val:,.2f}")

# 15. BRANDING & SIGNATURE
elif menu == "Company Branding & Signature":
    st.subheader("🖋️ Company Logo & Digital Signature")
    st.file_uploader("Upload Company Logo", type=["png", "jpg"])
    st.file_uploader("Upload Authorized Signature", type=["png", "jpg"])

# 16. CLOUD BACKUP
elif menu == "Automated Cloud Backup":
    st.subheader("☁️ Database Backup")
    conn = get_db()
    df_all = pd.read_sql_query("SELECT * FROM vouchers", conn)
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Backup CSV", data=csv, file_name="SD_Tally_Backup.csv", mime="text/csv")

# 17. ACCOUNT & BILLING
elif menu == "Account & Billing":
    st.subheader("💳 Account Subscription Details")
    st.write(f"**Current Status:** {sub_status}")
    st.write(f"**Registered Account:** `{st.session_state.user_mobile}`")
