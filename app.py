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

# Page Configuration & Executive High-Contrast Theme Setup
st.set_page_config(
    page_title="SD TALLY BUSINESS",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Custom Styling for Clear Readability & Card Visibility
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .stApp { background-color: #f8fafc; color: #0f172a; }
    
    /* Sidebar High-Visibility Text Fix */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Header Banner Styling */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 22px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { color: #38bdf8 !important; font-size: 2.1rem; font-weight: 700; margin: 0; }
    .main-header p { color: #94a3b8 !important; font-size: 0.95rem; margin-top: 4px; margin-bottom: 0; }

    /* Custom Cards for User & Subscription */
    .user-card {
        background-color: #f1f5f9;
        padding: 12px 15px;
        border-radius: 8px;
        border-left: 4px solid #0284c7;
        margin-bottom: 10px;
    }
    .plan-card {
        background-color: #e0f2fe;
        padding: 12px 15px;
        border-radius: 8px;
        color: #0369a1 !important;
        margin-bottom: 20px;
    }

    /* Metric Cards Styling Fix */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 18px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
        border-left: 5px solid #0284c7 !important;
        border: 1px solid #cbd5e1 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #0284c7;
        color: white !important;
        border-radius: 8px;
        height: 48px;
        font-weight: 700;
        border: none;
        width: 100%;
        box-shadow: 0 2px 4px rgba(2, 132, 199, 0.2);
    }
    .stButton>button:hover { background-color: #0369a1; }

    /* Thermal Receipt Formatting */
    .thermal-receipt {
        background-color: #ffffff;
        color: #000000;
        padding: 15px;
        border: 1px dashed #000;
        font-family: 'Courier New', Courier, monospace;
        width: 290px;
        margin: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Database Initialization (Multi-Tenant Engine with User Mobile Filtering)
DB_FILE = "sd_tally_v5_master.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    mobile TEXT PRIMARY KEY,
                    name TEXT,
                    business_name TEXT,
                    business_address TEXT,
                    gstin TEXT,
                    reg_date TEXT,
                    trial_end_date TEXT,
                    is_paid INTEGER DEFAULT 0,
                    paid_till TEXT,
                    role TEXT DEFAULT 'Owner'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
                    item_name TEXT,
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
                    user_mobile TEXT,
                    party_name TEXT,
                    gstin TEXT,
                    mobile TEXT,
                    party_type TEXT,
                    opening_balance REAL DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
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
                    user_mobile TEXT,
                    date TEXT,
                    account_type TEXT,
                    particulars TEXT,
                    amount REAL,
                    txn_type TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Session State Initializations
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "Owner"
if "business_name" not in st.session_state:
    st.session_state.business_name = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

def check_subscription_and_profile(mobile):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT reg_date, trial_end_date, is_paid, paid_till, role, business_name FROM users WHERE mobile=?", (mobile,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return "NEW_USER", None
    
    st.session_state.user_role = user[4] if len(user) > 4 and user[4] else "Owner"
    st.session_state.business_name = user[5] if len(user) > 5 and user[5] else None
    
    today = datetime.now().date()
    trial_end = datetime.strptime(user[0], "%Y-%m-%d").date()
    
    sub_status = "EXPIRED"
    if user[2] == 1 and user[3]:
        paid_till = datetime.strptime(user[3], "%Y-%m-%d").date()
        if today <= paid_till:
            sub_status = "ACTIVE_PRO"
    elif today <= trial_end:
        days_left = (trial_end - today).days
        sub_status = f"FREE_TRIAL ({days_left} days left)"
    
    return sub_status, st.session_state.business_name

# 1. LOGIN SCREEN
if not st.session_state.user_mobile:
    st.markdown("""
        <div class="main-header">
            <h1>💼 SD TALLY BUSINESS</h1>
            <p>Cloud ERP, Billing & Complete Accounting Suite</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, _ = st.columns([1, 1])
    with col1:
        st.subheader("🔑 Sign In with Mobile OTP")
        mobile = st.text_input("📱 Mobile Number", max_chars=10, placeholder="Enter 10-digit mobile number")
        
        if not st.session_state.otp_sent:
            if st.button("Send Verification OTP"):
                if len(mobile) == 10 and mobile.isdigit():
                    st.session_state.generated_otp = str(random.randint(1000, 9999))
                    st.session_state.otp_sent = True
                    st.info(f"🔑 Verification Testing OTP: **{st.session_state.generated_otp}**")
                else:
                    st.error("Please enter a valid 10-digit mobile number.")
        else:
            otp_in = st.text_input("🔑 Enter 4-Digit OTP")
            role_sel = st.selectbox("Select Access Role", ["Owner", "Salesman / Staff"])
            if st.button("Verify OTP & Continue"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.user_mobile = mobile
                    st.session_state.user_role = role_sel
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("SELECT mobile FROM users WHERE mobile=?", (mobile,))
                    if not c.fetchone():
                        today = datetime.now().date()
                        trial_end = today + timedelta(days=10)
                        c.execute("INSERT INTO users (mobile, name, reg_date, trial_end_date, is_paid, role) VALUES (?, ?, ?, ?, 0, ?)",
                                  (mobile, "Business User", str(today), str(trial_end), role_sel))
                        conn.commit()
                    conn.close()
                    st.rerun()
                else:
                    st.error("Invalid OTP entered.")
    st.stop()

# 2. CHECK PROFILE & ONBOARDING (BUSINESS PROFILE SETUP)
sub_status, bus_name = check_subscription_and_profile(st.session_state.user_mobile)

if not bus_name:
    st.markdown("""
        <div class="main-header">
            <h1>🏢 Business Profile Setup</h1>
            <p>Enter your business details to create your secure cloud ledger workspace</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📋 Business Onboarding Information")
    b_name = st.text_input("🏢 Business / Shop Name (e.g., Shree Ganesh Enterprises)")
    b_addr = st.text_area("📍 Business Address")
    b_gst = st.text_input("🧾 GSTIN Number (Optional)")
    
    if st.button("Save Business Profile & Launch"):
        if b_name:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET business_name=?, business_address=?, gstin=? WHERE mobile=?",
                      (b_name, b_addr, b_gst, st.session_state.user_mobile))
            conn.commit()
            conn.close()
            st.session_state.business_name = b_name
            st.success("✅ Business Profile Setup Complete!")
            st.rerun()
        else:
            st.error("Please enter your Business Name.")
    st.stop()

# 3. SIDEBAR WITH LOGOUT BUTTON
st.sidebar.markdown(f"""
    <div class="user-card">
        👤 <b>User:</b> {st.session_state.user_mobile}<br>
        🏢 <b>Business:</b> {st.session_state.business_name}
    </div>
    <div class="plan-card">
        🎁 <b>Plan:</b> {sub_status}
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout Account"):
    st.session_state.user_mobile = None
    st.session_state.business_name = None
    st.session_state.otp_sent = False
    st.rerun()

if sub_status == "EXPIRED":
    st.sidebar.error("❌ Subscription Expired")
    st.title("💳 Renewal Required")
    st.warning("Your trial has ended. Renew subscription for ₹95 + 18% GST (Total ₹112.10).")
    st.markdown("### **UPI ID: `8381085702@ibl`**")
    st.markdown("[👉 **Click Here to Send Proof on WhatsApp**](https://wa.me/918381085702?text=Hi,%20I%20have%20paid%20Rs.112.10%20for%20SD%20Tally%20Business.)")
    st.stop()

# 18 NAVIGATION MENU OPTIONS
if st.session_state.user_role == "Salesman / Staff":
    menu_options = [
        "🧾 Tax Invoice (Sales)",
        "📦 Barcode Quick Billing",
        "🖨️ Thermal Receipt Print"
    ]
else:
    menu_options = [
        "🏠 Dashboard",
        "🗂️ Masters (Items, HSN & Parties)",
        "🛒 Purchase Entry",
        "📥 Purchase & GSTR-2B Import",
        "🧾 Tax Invoice (Sales)",
        "📦 Barcode Quick Billing",
        "🖨️ Thermal Receipt Print",
        "💰 All Tally Vouchers (F4-F9)",
        "🏦 Capital & Bank Account Management",
        "📊 Bank Statement Excel Import",
        "👥 Receivables & Payment Reminders",
        "🧮 GST Reports (GSTR-1, 2B & 3B)",
        "🚚 e-Way Bill & e-Invoicing Portal",
        "📈 Profit & Loss Account",
        "📑 Balance Sheet",
        "☁️ Automated Cloud Backup",
        "🏢 Company Branding & Signature",
        "💳 Account & Billing"
    ]

menu = st.sidebar.radio("Navigation Menu", menu_options)

st.markdown(f"""
    <div class="main-header">
        <h1>{st.session_state.business_name}</h1>
        <p>SD TALLY BUSINESS Enterprise Workspace | User: {st.session_state.user_mobile}</p>
    </div>
""", unsafe_allow_html=True)

# ---------------- MODULES WITH USER-MOBILE ISOLATION ----------------

user_mob = st.session_state.user_mobile

# 1. DASHBOARD
if menu == "🏠 Dashboard":
    st.subheader("📊 Business Executive Dashboard")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice') AND user_mobile=?", conn, params=(user_mob,))
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase' AND user_mobile=?", conn, params=(user_mob,))
    bank_df = pd.read_sql_query("SELECT SUM(amount) as total FROM capital_bank_ledger WHERE account_type='Bank Account' AND user_mobile=?", conn, params=(user_mob,))
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    total_bank = bank_df['total'].iloc[0] or 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales Revenue", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchases", f"₹ {total_pur:,.2f}")
    c3.metric("Net Gross Profit", f"₹ {(total_sales - total_pur):,.2f}")
    c4.metric("Bank Balance", f"₹ {total_bank:,.2f}")

# 2. MASTERS
elif menu == "🗂️ Masters (Items, HSN & Parties)":
    st.subheader("⚙️ Masters Configuration")
    tab1, tab2 = st.tabs(["📦 Item & Stock Master", "👤 Party & Ledger Master"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        i_name = st.text_input("Item Name")
        b_code = st.text_input("Barcode ID Number", value=f"890{random.randint(100000, 999999)}")
        hsn = st.text_input("HSN / SAC Code", value="8517")
        c1, c2 = st.columns(2)
        godown = c1.text_input("Godown Location", value="Main Store")
        batch = c2.text_input("Batch Number", value="BATCH-01")
        
        c5, c6, c7, c8 = st.columns(4)
        s_price = c5.number_input("Selling Price", min_value=0.0)
        p_price = c6.number_input("Purchase Price", min_value=0.0)
        gst = c7.selectbox("GST %", [0.0, 5.0, 12.0, 18.0, 28.0])
        op_stock = c8.number_input("Opening Stock Qty", min_value=0.0)
        
        if st.button("Save Stock Item Master"):
            if i_name:
                c.execute("""INSERT INTO inventory (user_mobile, item_name, barcode, hsn_sac, godown, batch_no, expiry_date, sale_price, purchase_price, gst_rate, stock_qty, min_stock_alert)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (user_mob, i_name, b_code, hsn, godown, batch, str(datetime.now().date()), s_price, p_price, gst, op_stock, 5.0))
                conn.commit()
                st.success("Stock Master Item Saved!")
                    
    with tab2:
        p_name = st.text_input("Party / Customer Name")
        p_mobile = st.text_input("Mobile Number")
        p_gstin = st.text_input("GSTIN Number")
        p_type = st.selectbox("Party Classification", ["Customer", "Supplier"])
        
        if st.button("Save Ledger Master"):
            if p_name:
                c.execute("INSERT INTO parties (user_mobile, party_name, gstin, mobile, party_type, opening_balance) VALUES (?, ?, ?, ?, ?, ?)",
                          (user_mob, p_name, p_gstin, p_mobile, p_type, 0.0))
                conn.commit()
                st.success("Party Ledger Created!")

# 3. PURCHASE ENTRY
elif menu == "🛒 Purchase Entry":
    st.subheader("🛒 Purchase Voucher Entry")
    conn = get_db()
    c = conn.cursor()
    parties_list = [row[0] for row in c.execute("SELECT party_name FROM parties WHERE party_type='Supplier' AND user_mobile=?", (user_mob,)).fetchall()]
    items_list = [row[0] for row in c.execute("SELECT item_name FROM inventory WHERE user_mobile=?", (user_mob,)).fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Purchase Bill No", f"PUR-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    selected_party = c3.selectbox("Supplier Name", parties_list) if parties_list else c3.text_input("Supplier Name")
    
    selected_item = st.selectbox("Product Name", items_list) if items_list else st.text_input("Product Name")
    hsn = st.text_input("HSN Code", "9983")
    
    cq, cr, cg = st.columns(3)
    qty = cq.number_input("Qty Received", min_value=0.1, value=1.0)
    rate = cr.number_input("Purchase Rate per Unit (₹)", min_value=0.0, value=100.0)
    gst_rate = cg.number_input("GST %", value=18.0)

    taxable = qty * rate
    tax_amt = (taxable * gst_rate) / 100
    grand_total = taxable + tax_amt

    if st.button("Save Purchase Voucher"):
        c.execute("""INSERT INTO vouchers (user_mobile, voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (user_mob, "Purchase", v_no, str(v_date), selected_party, selected_item, hsn, qty, rate, taxable, gst_rate, tax_amt/2, tax_amt/2, 0.0, grand_total, "Credit"))
        c.execute("UPDATE inventory SET stock_qty = stock_qty + ? WHERE item_name = ? AND user_mobile = ?", (qty, selected_item, user_mob))
        conn.commit()
        st.success("✅ Purchase Saved & Stock Increased!")

# 4. TAX INVOICE (SALES)
elif menu == "🧾 Tax Invoice (Sales)":
    st.subheader("🧾 Create Tax Invoice")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties WHERE user_mobile=?", (user_mob,)).fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory WHERE user_mobile=?", (user_mob,)).fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Invoice Number", f"INV-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    selected_party = c3.selectbox("Customer Name", parties_list) if parties_list else c3.text_input("Customer Name")
    
    if items_list:
        selected_item = st.selectbox("Select Product", items_list)
        c = conn.cursor()
        c.execute("SELECT hsn_sac, sale_price, gst_rate, stock_qty FROM inventory WHERE item_name=? AND user_mobile=?", (selected_item, user_mob))
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

    if st.button("Save & Generate Tax Invoice"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (user_mobile, voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (user_mob, "Tax Invoice", v_no, str(v_date), selected_party, selected_item, hsn_sac, qty, rate, taxable, gst_rate, cgst, sgst, 0.0, grand_total, pay_mode))
        c.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ? AND user_mobile = ?", (qty, selected_item, user_mob))
        conn.commit()
        st.success(f"✅ Tax Invoice {v_no} Saved Successfully!")

# 5. ALL TALLY VOUCHERS
elif menu == "💰 All Tally Vouchers (F4-F9)":
    st.subheader("💰 Tally Accounting Vouchers")
    v_type = st.selectbox("Select Voucher Type", ["Receipt (F6)", "Payment (F5)", "Contra (F4)", "Journal (F7)", "Credit Note", "Debit Note"])
    
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties WHERE user_mobile=?", (user_mob,)).fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Voucher No", f"{v_type[:3].upper()}-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    party = c3.selectbox("Ledger Account", parties_list) if parties_list else c3.text_input("Ledger Account")
    
    amt = st.number_input("Amount (₹)", min_value=1.0)
    narration = st.text_area("Narration / Remarks")
    
    if st.button("Post Voucher Entry"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (user_mobile, voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, '9983', 0, 0, ?, 0, 0, 0, 0, ?, ?)""",
                  (user_mob, v_type, v_no, str(v_date), party, narration, amt, amt, "Bank/Cash"))
        conn.commit()
        st.success(f"✅ {v_type} Entry Posted!")

# REST OF MODULES...
elif menu == "📥 Purchase & GSTR-2B Import":
    st.subheader("📥 GSTR-2B Import")
    st.file_uploader("Upload GSTR-2B File", type=["csv", "xlsx"])

elif menu == "📦 Barcode Quick Billing":
    st.subheader("📦 Barcode Camera Billing Scanner")
    st.text_input("Scan Barcode ID")

elif menu == "🖨️ Thermal Receipt Print":
    st.subheader("🖨️ POS Thermal Printer Receipt Generator")
    conn = get_db()
    vouchers = pd.read_sql_query("SELECT voucher_no, party_name, total_amt FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    st.dataframe(vouchers, use_container_width=True)

elif menu == "🏦 Capital & Bank Account Management":
    st.subheader("🏦 Capital Account & Bank Ledger")
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM capital_bank_ledger WHERE user_mobile=?", conn, params=(user_mob,))
    st.dataframe(df, use_container_width=True)

elif menu == "📊 Bank Statement Excel Import":
    st.subheader("📊 Import Bank Statement")
    st.file_uploader("Choose File", type=["xlsx", "csv"])

elif menu == "👥 Receivables & Payment Reminders":
    st.subheader("👥 Outstanding Receivables")
    conn = get_db()
    df = pd.read_sql_query("SELECT party_name, SUM(total_amt) as pending FROM vouchers WHERE payment_mode='Credit (Pending)' AND user_mobile=? GROUP BY party_name", conn, params=(user_mob,))
    st.dataframe(df, use_container_width=True)

elif menu == "🧮 GST Reports (GSTR-1, 2B & 3B)":
    st.subheader("🧮 Statutory GST Reports Hub")
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    st.dataframe(df, use_container_width=True)

elif menu == "🚚 e-Way Bill & e-Invoicing Portal":
    st.subheader("🚚 Government e-Way Bill")
    conn = get_db()
    vouchers = pd.read_sql_query("SELECT voucher_no, party_name, total_amt FROM vouchers WHERE total_amt >= 50000 AND user_mobile=?", conn, params=(user_mob,))
    st.dataframe(vouchers, use_container_width=True)

elif menu == "📈 Profit & Loss Account":
    st.subheader("📈 Profit & Loss Account Statement")
    conn = get_db()
    sales = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice') AND user_mobile=?", conn, params=(user_mob,)).iloc[0, 0] or 0.0
    purchases = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Purchase' AND user_mobile=?", conn, params=(user_mob,)).iloc[0, 0] or 0.0
    st.metric("Net Operating Profit", f"₹ {(sales - purchases):,.2f}")

elif menu == "📑 Balance Sheet":
    st.subheader("📑 Enterprise Balance Sheet")
    conn = get_db()
    stock_val = pd.read_sql_query("SELECT SUM(stock_qty * purchase_price) FROM inventory WHERE user_mobile=?", conn, params=(user_mob,)).iloc[0, 0] or 0.0
    st.metric("Total Closing Stock Value", f"₹ {stock_val:,.2f}")

elif menu == "☁️ Automated Cloud Backup":
    st.subheader("☁️ Database Backup")
    conn = get_db()
    df_all = pd.read_sql_query("SELECT * FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Backup CSV", data=csv, file_name=f"{st.session_state.business_name}_Backup.csv", mime="text/csv")

elif menu == "🏢 Company Branding & Signature":
    st.subheader("🏢 Company Logo & Authorized Signature")
    st.file_uploader("Upload Company Logo", type=["png", "jpg"])

elif menu == "💳 Account & Billing":
    st.subheader("💳 Account Subscription Details")
    st.write(f"**Current Status:** {sub_status}")
    st.write(f"**Business Name:** `{st.session_state.business_name}`")
    st.write(f"**Registered Account:** `{st.session_state.user_mobile}`")
