import streamlit as st
import pandas as pd
import sqlite3
import random
import io
import json
import base64
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None

# Page Setup & Mobile Touch Styling
st.set_page_config(
    page_title="SD TALLY BUSINESS Enterprise",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# 🛠️ PROFESSIONAL MOBILE SCROLLING & TOUCH CSS
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp, .main {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        touch-action: pan-y !important;
    }
    .stApp { background-color: #f8fafc; color: #0f172a; }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff; padding: 22px; border-radius: 12px; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { color: #38bdf8 !important; font-size: 2.1rem; font-weight: 700; margin: 0; }
    .main-header p { color: #94a3b8 !important; font-size: 0.95rem; margin-top: 4px; margin-bottom: 0; }

    .user-card {
        background-color: #f1f5f9; padding: 12px 15px; border-radius: 8px;
        border-left: 4px solid #0284c7; margin-bottom: 10px;
    }
    .plan-card {
        background-color: #e0f2fe; padding: 12px 15px; border-radius: 8px;
        color: #0369a1 !important; margin-bottom: 20px;
    }

    [data-testid="stMetric"] {
        background-color: #ffffff !important; padding: 18px !important; border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important; border-left: 5px solid #0284c7 !important;
        border: 1px solid #cbd5e1 !important;
    }
    [data-testid="stMetricLabel"] { color: #475569 !important; font-size: 1.05rem !important; font-weight: 700 !important; }
    [data-testid="stMetricValue"] { color: #0f172a !important; font-size: 1.8rem !important; font-weight: 800 !important; }

    .stButton>button {
        background-color: #0284c7; color: white !important; border-radius: 8px;
        height: 48px; font-weight: 700; border: none; width: 100%;
        box-shadow: 0 2px 4px rgba(2, 132, 199, 0.2);
    }
    .stButton>button:hover { background-color: #0369a1; }
    </style>
""", unsafe_allow_html=True)

# Database Initialization
DB_FILE = "sd_tally_v30_ultimate.db"

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
                    unit TEXT DEFAULT 'PCS',
                    barcode TEXT,
                    hsn_sac TEXT,
                    godown TEXT DEFAULT 'Main Store',
                    batch_no TEXT,
                    expiry_date TEXT,
                    sale_price REAL,
                    purchase_price REAL,
                    gst_rate REAL,
                    stock_qty REAL,
                    min_stock_alert REAL DEFAULT 5,
                    is_active INTEGER DEFAULT 1
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS godowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
                    godown_name TEXT,
                    address TEXT,
                    is_active INTEGER DEFAULT 1
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
                    party_name TEXT,
                    gstin TEXT,
                    mobile TEXT,
                    party_type TEXT,
                    opening_balance REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
                    bank_name TEXT,
                    account_no TEXT,
                    ifsc_code TEXT,
                    branch_name TEXT,
                    opening_balance REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
                    voucher_type TEXT,
                    voucher_no TEXT,
                    date TEXT,
                    party_name TEXT,
                    item_name TEXT,
                    unit TEXT DEFAULT 'PCS',
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
                    irn_no TEXT,
                    debit_account TEXT,
                    credit_account TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS capital_bank_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_mobile TEXT,
                    date TEXT,
                    account_type TEXT,
                    particulars TEXT,
                    amount REAL,
                    txn_type TEXT,
                    bank_name TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS branding (
                    user_mobile TEXT PRIMARY KEY,
                    logo_base64 TEXT,
                    sig_base64 TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Safe Session Initializations
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "Owner"
if "business_name" not in st.session_state:
    st.session_state.business_name = None
if "business_gstin" not in st.session_state:
    st.session_state.business_gstin = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "cart_items" not in st.session_state:
    st.session_state.cart_items = []

# 🔑 PERSISTENT SESSION RESTORE ENGINE (NO-LOGOUT BACK FIX)
try:
    query_params = st.query_params
    saved_mobile = query_params.get("user_session", None)
    if not st.session_state.user_mobile and saved_mobile:
        st.session_state.user_mobile = str(saved_mobile)
except Exception:
    pass

def check_subscription_and_profile(mobile):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT reg_date, trial_end_date, is_paid, paid_till, role, business_name, gstin FROM users WHERE mobile=?", (mobile,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return "NEW_USER", None
    
    st.session_state.user_role = user[4] if len(user) > 4 and user[4] else "Owner"
    st.session_state.business_name = user[5] if len(user) > 5 and user[5] else None
    st.session_state.business_gstin = user[6] if len(user) > 6 and user[6] else "URP"
    
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

# LOGIN SCREEN
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
            if st.button("Verify OTP & Open Workspace"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.user_mobile = mobile
                    st.session_state.user_role = role_sel
                    try:
                        st.query_params["user_session"] = mobile
                    except Exception:
                        pass
                    
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

# CHECK PROFILE & ONBOARDING
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
            st.session_state.business_gstin = b_gst
            st.success("✅ Business Profile Setup Complete!")
            st.rerun()
        else:
            st.error("Please enter your Business Name.")
    st.stop()

# SIDEBAR WORKSPACE
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
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.rerun()

if sub_status == "EXPIRED":
    st.sidebar.error("❌ Subscription Expired")
    st.title("💳 Renewal Required")
    st.warning("Your trial has ended. Renew subscription for ₹95 + 18% GST (Total ₹112.10).")
    st.markdown("### **UPI ID: `8381085702@ibl`**")
    
    wa_renew_msg = urllib.parse.quote(f"Hi, I have paid Rs.112.10 for SD Tally Business renewal for Mobile: {st.session_state.user_mobile}")
    st.markdown(f"[👉 **Click Here to Send Proof on WhatsApp**](https://wa.me/918381085702?text={wa_renew_msg})")
    st.stop()

# NAVIGATION MENU WITH ALL 30 MODULES
menu_options = [
    "🏠 Dashboard",
    "📁 Masters (Items, Godowns & Parties)",
    "🛒 Purchase Entry",
    "📥 Purchase & GSTR-2B Import",
    "🧾 Tax Invoice (Sales)",
    "📦 Barcode Quick Billing",
    "🖨️ Thermal Receipt Print",
    "💰 All Tally Vouchers (F4-F9)",
    "🏦 Capital & Bank Account Management",
    "📊 Bank Statement Excel Import",
    "👥 Receivables & Party Statements",
    "🧮 GST Reports (GSTR-1, 2B & 3B)",
    "🚚 e-Way Bill & e-Invoicing Portal",
    "📈 Profit & Loss Account",
    "📋 Balance Sheet",
    "☁️ Automated Cloud Backup",
    "🏢 Company Branding & Signature",
    "💳 Account & Billing",
    "📦 Stock Summary & Stock Ledger",
    "🔄 Sales Return & Purchase Return",
    "💸 Payment & Receipt Management",
    "📅 Day Book",
    "📒 Ledger & Trial Balance",
    "📑 Outstanding Receivable & Payable",
    "🔍 Voucher Search / Edit / Delete",
    "📊 Business Dashboard & Reports",
    "🔐 User & Permission Management",
    "⚙️ Company Settings",
    "🖨️ Print & PDF Export",
    "📤 Excel / PDF Report Export"
]

menu = st.sidebar.radio("Navigation Menu", menu_options)

st.markdown(f"""
    <div class="main-header">
        <h1>{st.session_state.business_name}</h1>
        <p>SD TALLY BUSINESS Enterprise Workspace | Account: {st.session_state.user_mobile}</p>
    </div>
""", unsafe_allow_html=True)

user_mob = st.session_state.user_mobile

# ---------------- MODULE IMPLEMENTATIONS ----------------

# 1. DASHBOARD
if menu == "🏠 Dashboard" or menu == "📊 Business Dashboard & Reports":
    st.subheader("📊 Business Executive Dashboard & Analytics")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice') AND user_mobile=?", conn, params=(user_mob,))
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase' AND user_mobile=?", conn, params=(user_mob,))
    bank_df = pd.read_sql_query("SELECT SUM(opening_balance) as total FROM bank_accounts WHERE user_mobile=?", conn, params=(user_mob,))
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    total_bank = bank_df['total'].iloc[0] or 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales Revenue", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchases", f"₹ {total_pur:,.2f}")
    c3.metric("Net Gross Profit", f"₹ {(total_sales - total_pur):,.2f}")
    c4.metric("Bank Balance", f"₹ {total_bank:,.2f}")
    
    st.markdown("---")
    st.subheader("📈 Monthly Performance Overview")
    chart_data = pd.DataFrame({
        "Category": ["Total Revenue", "Total Purchases", "Operating Profit"],
        "Amount (₹)": [total_sales, total_pur, max(0, total_sales - total_pur)]
    })
    st.bar_chart(chart_data.set_index("Category"))

# 2. MASTERS
elif menu == "📁 Masters (Items, Godowns & Parties)":
    st.subheader("⚙️ Masters Configuration")
    tab1, tab2, tab3 = st.tabs(["📦 Add Stock Item", "🏢 Godown Master", "👤 Add Party Ledger"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        u1, u2 = st.columns([3, 1])
        i_name = u1.text_input("Item Name")
        i_unit = u2.selectbox("Unit (UOM)", ["PCS", "KG", "LTR", "MTR", "BOX", "SQFT", "BAG", "PACK"])
        s_price = st.number_input("Selling Price (₹)", min_value=0.0)
        p_price = st.number_input("Purchase Price (₹)", min_value=0.0)
        gst = st.selectbox("GST %", [0.0, 5.0, 12.0, 18.0, 28.0])
        op_stock = st.number_input("Opening Stock Qty", min_value=0.0)
        
        if st.button("Save Stock Item Master"):
            if i_name:
                c.execute("""INSERT INTO inventory (user_mobile, item_name, unit, sale_price, purchase_price, gst_rate, stock_qty)
                             VALUES (?, ?, ?, ?, ?, ?, ?)""", (user_mob, i_name, i_unit, s_price, p_price, gst, op_stock))
                conn.commit()
                st.success("Stock Master Saved!")

    with tab2:
        g_name = st.text_input("Godown Name")
        g_addr = st.text_area("Address")
        if st.button("Save Godown"):
            c.execute("INSERT INTO godowns (user_mobile, godown_name, address) VALUES (?, ?, ?)", (user_mob, g_name, g_addr))
            conn.commit()
            st.success("Godown Saved!")

    with tab3:
        p_name = st.text_input("Party Name")
        p_type = st.selectbox("Party Type", ["Customer", "Supplier"])
        p_bal = st.number_input("Opening Balance (₹)", min_value=0.0)
        if st.button("Save Party"):
            c.execute("INSERT INTO parties (user_mobile, party_name, party_type, opening_balance) VALUES (?, ?, ?, ?)", (user_mob, p_name, p_type, p_bal))
            conn.commit()
            st.success("Party Ledger Created!")

# 3. STOCK SUMMARY & LEDGER
elif menu == "📦 Stock Summary & Stock Ledger":
    st.subheader("📦 Stock Inventory Summary")
    conn = get_db()
    df_stock = pd.read_sql_query("SELECT item_name, unit, sale_price, purchase_price, stock_qty FROM inventory WHERE user_mobile=?", conn, params=(user_mob,))
    st.dataframe(df_stock, use_container_width=True)

# 4. SALES RETURN & PURCHASE RETURN
elif menu == "🔄 Sales Return & Purchase Return":
    st.subheader("🔄 Credit Note (Sales Return) & Debit Note (Purchase Return)")
    st.info("Record Sales Return (F8) or Purchase Return (F9) under All Tally Vouchers module.")

# 5. DAY BOOK
elif menu == "📅 Day Book":
    st.subheader("📅 Daily Accounting Day Book")
    conn = get_db()
    df_day = pd.read_sql_query("SELECT date, voucher_type, voucher_no, party_name, total_amt, payment_mode FROM vouchers WHERE user_mobile=? ORDER BY date DESC", conn, params=(user_mob,))
    st.dataframe(df_day, use_container_width=True)

# 6. LEDGER & TRIAL BALANCE
elif menu == "📒 Ledger & Trial Balance":
    st.subheader("📒 Trial Balance Statement")
    conn = get_db()
    df_v = pd.read_sql_query("SELECT debit_account as Ledger, SUM(total_amt) as Debit_Total FROM vouchers WHERE user_mobile=? GROUP BY debit_account", conn, params=(user_mob,))
    st.dataframe(df_v, use_container_width=True)

# 7. OUTSTANDING RECEIVABLES & PAYABLES
elif menu == "👥 Receivables & Party Statements" or menu == "📑 Outstanding Receivable & Payable":
    st.subheader("👥 Customer Receivables & Supplier Payables")
    conn = get_db()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Customer Outstanding")
        cust_df = pd.read_sql_query("SELECT party_name, SUM(total_amt) as Pending FROM vouchers WHERE payment_mode='Credit (Pending)' AND user_mobile=? GROUP BY party_name", conn, params=(user_mob,))
        st.dataframe(cust_df, use_container_width=True)
    with c2:
        st.markdown("### Supplier Outstanding")
        supp_df = pd.read_sql_query("SELECT party_name, SUM(total_amt) as Pending FROM vouchers WHERE voucher_type='Purchase' AND payment_mode='Credit' AND user_mobile=? GROUP BY party_name", conn, params=(user_mob,))
        st.dataframe(supp_df, use_container_width=True)

# 8. VOUCHER SEARCH / EDIT / DELETE
elif menu == "🔍 Voucher Search / Edit / Delete":
    st.subheader("🔍 Voucher Register & Edit Actions")
    conn = get_db()
    c = conn.cursor()
    df_all_v = pd.read_sql_query("SELECT id, voucher_type, voucher_no, date, party_name, total_amt FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    st.dataframe(df_all_v, use_container_width=True)
    if not df_all_v.empty:
        del_id = st.selectbox("Select Voucher ID to Delete", df_all_v['id'].tolist())
        if st.button("🗑️ Delete Voucher Entry"):
            c.execute("DELETE FROM vouchers WHERE id=? AND user_mobile=?", (del_id, user_mob))
            conn.commit()
            st.success("Voucher Entry Deleted!")
            st.rerun()

# 9. USER PERMISSION & SETTINGS
elif menu == "🔐 User & Permission Management" or menu == "⚙️ Company Settings":
    st.subheader("⚙️ Company Settings & User Permissions")
    st.write(f"**Business Name:** {st.session_state.business_name}")
    st.write(f"**GSTIN:** {st.session_state.business_gstin}")
    st.write(f"**Role:** {st.session_state.user_role}")

# 10. PRINT / PDF / EXCEL EXPORT
elif menu == "🖨️ Print & PDF Export" or menu == "📤 Excel / PDF Report Export":
    st.subheader("📤 Export Financial Reports (CSV / Excel)")
    conn = get_db()
    df_exp = pd.read_sql_query("SELECT * FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    csv_exp = df_exp.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Master Report (CSV)", data=csv_exp, file_name="SD_Tally_Report.csv", mime="text/csv")

# DEFAULT FALLBACK FOR OTHER MENUS (TAX INVOICE, PURCHASE, GST, BACKUP ETC.)
elif menu == "🧾 Tax Invoice (Sales)":
    st.subheader("🧾 Create Multi-Item Tax Invoice")
    conn = get_db()
    c = conn.cursor()
    v_no = st.text_input("Invoice Number", f"INV-{random.randint(1000,9999)}")
    p_name = st.text_input("Customer Name")
    amt = st.number_input("Invoice Amount (₹)", min_value=1.0)
    p_mode = st.selectbox("Payment Mode", ["Bank / UPI", "Cash", "Credit (Pending)"])
    if st.button("Save Sales Invoice"):
        c.execute("INSERT INTO vouchers (user_mobile, voucher_type, voucher_no, date, party_name, total_amt, payment_mode) VALUES (?, 'Tax Invoice', ?, ?, ?, ?, ?)",
                  (user_mob, v_no, str(datetime.now().date()), p_name, amt, p_mode))
        conn.commit()
        st.success(f"Invoice {v_no} Saved Successfully!")

elif menu == "🖨️ Thermal Receipt Print":
    st.subheader("🖨️ POS 58mm Thermal Printer Receipt")
    conn = get_db()
    df_v = pd.read_sql_query("SELECT voucher_no, party_name, total_amt FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    if not df_v.empty:
        sel_v = st.selectbox("Select Invoice", df_v['voucher_no'].tolist())
        row = df_v[df_v['voucher_no'] == sel_v].iloc[0]
        html_r = f"""
        <div style="background:#fff; padding:15px; border:1px dashed #000; font-family:monospace; width:260px; margin:auto;">
            <center><h3>{st.session_state.business_name}</h3><p>Retail Invoice</p></center>
            <p>Inv: {row['voucher_no']}</p>
            <p>Customer: {row['party_name']}</p>
            <hr>
            <h3>Total: Rs. {row['total_amt']:,.2f}</h3>
            <center><p>Thank You!</p></center>
        </div>
        """
        components.html(html_r, height=300)

elif menu == "☁️ Automated Cloud Backup":
    st.subheader("☁️ Database Backup & Export")
    conn = get_db()
    df_all = pd.read_sql_query("SELECT * FROM vouchers WHERE user_mobile=?", conn, params=(user_mob,))
    csv_data = df_all.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Database Backup (CSV)", data=csv_data, file_name=f"{st.session_state.business_name}_Backup.csv", mime="text/csv")
