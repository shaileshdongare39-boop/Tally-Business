import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None

# Page Configuration & Modern Theme Setup
st.set_page_config(
    page_title="SD TALLY BUSINESS - Enterprise ERP",
    layout="wide",
    page_icon="💼",
    initial_sidebar_state="expanded"
)

# Custom Professional CSS for UI Enhancement
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0d6efd;
    }
    .css-1d3912e { background-color: #0d1b2a; }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 45px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Database Initialization
DB_FILE = "tally_business_master.db"

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
                    paid_till TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT UNIQUE,
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
                    qty REAL,
                    rate REAL,
                    taxable_amt REAL,
                    gst_rate REAL,
                    cgst REAL,
                    sgst REAL,
                    igst REAL,
                    total_amt REAL,
                    payment_mode TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Session State for Authentication
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

def check_subscription(mobile):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT reg_date, trial_end_date, is_paid, paid_till FROM users WHERE mobile=?", (mobile,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return "NEW_USER"
    
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

# LOGIN / REGISTER SCREEN
if not st.session_state.user_mobile:
    st.title("💼 SD TALLY BUSINESS")
    st.subheader("Cloud Accounting & ERP Management Suite")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        mobile = st.text_input("📱 Enter Mobile Number", max_chars=10)
        
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
            if st.button("Verify OTP & Login"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.user_mobile = mobile
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("SELECT mobile FROM users WHERE mobile=?", (mobile,))
                    if not c.fetchone():
                        today = datetime.now().date()
                        trial_end = today + timedelta(days=10)
                        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, 0, NULL)",
                                  (mobile, "Business Owner", str(today), str(trial_end)))
                        conn.commit()
                    conn.close()
                    st.rerun()
                else:
                    st.error("Incorrect OTP entered!")
    st.stop()

# SUBSCRIPTION & USER STATUS CHECK
sub_status = check_subscription(st.session_state.user_mobile)
st.sidebar.markdown(f"👤 **Account:** `{st.session_state.user_mobile}`")

if "FREE_TRIAL" in sub_status:
    st.sidebar.info(f"🎁 Plan: {sub_status}")
elif sub_status == "ACTIVE_PRO":
    st.sidebar.success("🌟 Active PRO Subscription")
elif sub_status == "EXPIRED":
    st.sidebar.error("❌ Subscription Expired")
    st.title("💳 Plan Renewal Required")
    st.warning("Your 10-day trial period has ended. Please renew subscription for ₹95 + 18% GST (Total ₹112.10).")
    
    st.markdown("---")
    st.subheader("📲 Instant UPI Payment")
    st.markdown("### **UPI ID: `8381085702@ibl`**")
    st.write("Amount Payable: **₹ 112.10**")
    
    st.info("💡 After payment, click the button below to send payment screenshot on WhatsApp:")
    st.markdown("[👉 **Click Here to Send Payment Proof on WhatsApp**](https://wa.me/918381085702?text=Hi,%20I%20have%20paid%20Rs.112.10%20for%20Tally%20App.%20Please%20activate%20my%20account.)")
    st.stop()

# MAIN NAVIGATION MENU
st.sidebar.title("🏢 SD TALLY BUSINESS")
menu = st.sidebar.radio("Navigation Menu", [
    "Dashboard",
    "Sales Invoice",
    "Purchase Entry",
    "All Tally Vouchers (F4-F9)",
    "Masters (Items & Parties)",
    "Receivables & Payment Reminders",
    "GST Reports (GSTR-1 & 3B)",
    "Profit & Loss Account",
    "Balance Sheet",
    "Account & Billing"
])

# 1. DASHBOARD
if menu == "Dashboard":
    st.title("📊 Executive Dashboard")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type IN ('Sales', 'Sales Invoice')", conn)
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase'", conn)
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales Revenue", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchase Expenditure", f"₹ {total_pur:,.2f}")
    c3.metric("Net Operating Profit", f"₹ {(total_sales - total_pur):,.2f}")
    
    st.markdown("---")
    st.subheader("⚠️ Inventory Low Stock Monitor")
    low_stock = pd.read_sql_query("SELECT item_name, godown, stock_qty, min_stock_alert FROM inventory WHERE stock_qty <= min_stock_alert", conn)
    if not low_stock.empty:
        st.warning("Low stock items detected:")
        st.dataframe(low_stock, use_container_width=True)
    else:
        st.success("All inventory stock levels are optimal.")

# 2. SALES INVOICE
elif menu == "Sales Invoice":
    st.title("🧾 Quick Sales Invoice")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Invoice Number", f"INV-{random.randint(1000,9999)}")
    v_date = c2.date_input("Invoice Date", datetime.now())
    selected_party = c3.selectbox("Customer Name", parties_list) if parties_list else c3.text_input("Customer Name")
    
    if items_list:
        selected_item = st.selectbox("Select Product / Item", items_list)
        c = conn.cursor()
        c.execute("SELECT sale_price, gst_rate, stock_qty FROM inventory WHERE item_name=?", (selected_item,))
        item_data = c.fetchone()
        default_rate, default_gst, curr_stock = item_data[0], item_data[1], item_data[2]
        st.caption(f"Stock Available: **{curr_stock}** units")
    else:
        selected_item = st.text_input("Product Name")
        default_rate, default_gst = 100.0, 18.0

    cq, cr, cg, cp = st.columns(4)
    qty = cq.number_input("Quantity", min_value=0.1, value=1.0)
    rate = cr.number_input("Rate per Unit (₹)", min_value=0.0, value=float(default_rate))
    gst_rate = cg.number_input("GST Rate (%)", value=float(default_gst))
    pay_mode = cp.selectbox("Payment Mode", ["Cash", "UPI / Online", "Credit (Pending)"])

    taxable = qty * rate
    cgst = (taxable * (gst_rate / 2)) / 100
    sgst = (taxable * (gst_rate / 2)) / 100
    grand_total = taxable + cgst + sgst

    st.markdown("### 💰 Invoice Total Summary")
    st.subheader(f"Grand Total: ₹ {grand_total:,.2f}")

    if st.button("Save & Generate Invoice"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("Sales Invoice", v_no, str(v_date), selected_party, selected_item, qty, rate, taxable, gst_rate, cgst, sgst, 0.0, grand_total, pay_mode))
        c.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ?", (qty, selected_item))
        conn.commit()
        st.success(f"✅ Sales Invoice {v_no} Saved Successfully!")
        
        wa_text = f"Hello {selected_party}, your invoice {v_no} of Rs.{grand_total:.2f} has been generated. Thank you!"
        st.markdown(f"[📲 **Share Invoice via WhatsApp**](https://wa.me/?text={wa_text})")

# 3. PURCHASE ENTRY
elif menu == "Purchase Entry":
    st.title("🛒 Purchase Voucher Entry")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties WHERE party_type='Supplier'").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Purchase Bill No", f"PUR-{random.randint(1000,9999)}")
    v_date = c2.date_input("Purchase Date", datetime.now())
    selected_party = c3.selectbox("Supplier Name", parties_list) if parties_list else c3.text_input("Supplier Name")
    
    selected_item = st.selectbox("Product Name", items_list) if items_list else st.text_input("Product Name")
    cq, cr, cg = st.columns(3)
    qty = cq.number_input("Qty Received", min_value=0.1, value=1.0)
    rate = cr.number_input("Purchase Rate", min_value=0.0, value=100.0)
    gst_rate = cg.number_input("GST %", value=18.0)

    taxable = qty * rate
    total_tax = (taxable * gst_rate) / 100
    grand_total = taxable + total_tax

    if st.button("Save Purchase Voucher"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("Purchase", v_no, str(v_date), selected_party, selected_item, qty, rate, taxable, gst_rate, total_tax/2, total_tax/2, 0.0, grand_total, "Credit"))
        c.execute("UPDATE inventory SET stock_qty = stock_qty + ? WHERE item_name = ?", (qty, selected_item))
        conn.commit()
        st.success("✅ Purchase Voucher Saved & Inventory Stock Updated!")

# 4. ALL TALLY VOUCHERS
elif menu == "All Tally Vouchers (F4-F9)":
    st.title("📑 Professional Tally Voucher Registry")
    v_type = st.selectbox("Select Voucher Type", ["Receipt (F6)", "Payment (F5)", "Contra (F4)", "Journal (F7)", "Credit Note", "Debit Note"])
    
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Voucher No", f"{v_type[:3].upper()}-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    party = c3.selectbox("Ledger / Party Account", parties_list) if parties_list else c3.text_input("Ledger Account")
    
    amt = st.number_input("Transaction Amount (₹)", min_value=1.0)
    narration = st.text_area("Narration / Entry Particulars")
    
    if st.button("Post Voucher Entry"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, 0, 0, ?, 0, 0, 0, 0, ?, ?)""",
                  (v_type, v_no, str(v_date), party, narration, amt, amt, "Bank/Cash"))
        conn.commit()
        st.success(f"✅ {v_type} Entry Posted Successfully!")

# 5. MASTERS CREATION
elif menu == "Masters (Items & Parties)":
    st.title("⚙️ Master Configuration")
    tab1, tab2 = st.tabs(["📦 Stock & Inventory Master", "👤 Party & Ledger Master"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        i_name = st.text_input("Item / Product Name")
        c1, c2, c3, c4 = st.columns(4)
        godown = c1.text_input("Godown Location", value="Main Warehouse")
        batch = c2.text_input("Batch Number", value="BATCH-01")
        exp_date = c3.date_input("Expiry Date", datetime.now() + timedelta(days=365))
        min_stock = c4.number_input("Low Stock Threshold Alert", value=5.0)
        
        c5, c6, c7, c8 = st.columns(4)
        s_price = c5.number_input("Selling Price", min_value=0.0)
        p_price = c6.number_input("Purchase Price", min_value=0.0)
        gst = c7.selectbox("GST %", [0.0, 5.0, 12.0, 18.0, 28.0])
        op_stock = c8.number_input("Opening Stock Quantity", min_value=0.0)
        
        if st.button("Save Item Master"):
            if i_name:
                try:
                    c.execute("""INSERT INTO inventory (item_name, godown, batch_no, expiry_date, sale_price, purchase_price, gst_rate, stock_qty, min_stock_alert)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (i_name, godown, batch, str(exp_date), s_price, p_price, gst, op_stock, min_stock))
                    conn.commit()
                    st.success("Master Stock Item Saved!")
                except sqlite3.IntegrityError:
                    st.error("Item name already exists.")
                    
    with tab2:
        p_name = st.text_input("Party / Customer Name")
        p_mobile = st.text_input("Mobile Number")
        p_gstin = st.text_input("GSTIN Number")
        p_type = st.selectbox("Party Classification", ["Customer", "Supplier"])
        op_bal = st.number_input("Opening Balance (₹)", value=0.0)
        
        if st.button("Save Ledger Master"):
            if p_name:
                try:
                    c.execute("INSERT INTO parties (party_name, gstin, mobile, party_type, opening_balance) VALUES (?, ?, ?, ?, ?)",
                              (p_name, p_gstin, p_mobile, p_type, op_bal))
                    conn.commit()
                    st.success("Master Ledger Account Created!")
                except sqlite3.IntegrityError:
                    st.error("Party name already exists.")

# 6. RECEIVABLES & REMINDERS
elif menu == "Receivables & Payment Reminders":
    st.title("📒 Receivables & Outstanding Register")
    conn = get_db()
    udhari_df = pd.read_sql_query("SELECT party_name, payment_mode, SUM(total_amt) as pending_amount FROM vouchers WHERE payment_mode='Credit (Pending)' GROUP BY party_name", conn)
    
    st.subheader("Pending Customer Receivables")
    st.dataframe(udhari_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📲 Send Payment Reminder")
    selected_p = st.selectbox("Select Customer to Send Reminder", udhari_df['party_name'].tolist()) if not udhari_df.empty else None
    if selected_p:
        amt = udhari_df[udhari_df['party_name'] == selected_p]['pending_amount'].iloc[0]
        rem_text = f"Dear {selected_p}, your outstanding payment of Rs.{amt:.2f} is pending. Kindly pay via UPI to 8381085702@ibl. Thank you!"
        st.markdown(f"[📲 **Send Payment Reminder on WhatsApp**](https://wa.me/?text={rem_text})")

# 7. GST REPORTS
elif menu == "GST Reports (GSTR-1 & 3B)":
    st.title("📑 Statutory GST Reports")
    conn = get_db()
    df = pd.read_sql_query("SELECT date, voucher_no, voucher_type, party_name, taxable_amt, gst_rate, cgst, sgst, igst, total_amt FROM vouchers", conn)
    st.dataframe(df, use_container_width=True)

# 8. PROFIT & LOSS ACCOUNT
elif menu == "Profit & Loss Account":
    st.title("📊 Financial Statement: Profit & Loss Account")
    conn = get_db()
    sales = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type IN ('Sales', 'Sales Invoice')", conn).iloc[0, 0] or 0.0
    purchases = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Purchase'", conn).iloc[0, 0] or 0.0
    
    st.write(f"**Total Revenue (Sales):** ₹ {sales:,.2f}")
    st.write(f"**Cost of Goods Sold (Purchases):** ₹ {purchases:,.2f}")
    st.markdown("---")
    st.metric("Net Operating Profit", f"₹ {(sales - purchases):,.2f}")

# 9. BALANCE SHEET
elif menu == "Balance Sheet":
    st.title("⚖️ Financial Statement: Balance Sheet")
    conn = get_db()
    stock_val = pd.read_sql_query("SELECT SUM(stock_qty * purchase_price) FROM inventory", conn).iloc[0, 0] or 0.0
    cash_bank = pd.read_sql_query("SELECT SUM(total_amt) FROM vouchers WHERE payment_mode IN ('Cash', 'Bank/Cash', 'UPI / Online')", conn).iloc[0, 0] or 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Assets: Closing Inventory Stock Value", f"₹ {stock_val:,.2f}")
    col2.metric("Assets: Cash & Bank Balances", f"₹ {cash_bank:,.2f}")

# 10. ACCOUNT & BILLING
elif menu == "Account & Billing":
    st.title("💳 Subscription & Billing Configuration")
    st.write(f"**Current Status:** {sub_status}")
    st.write(f"**Registered Account:** `{st.session_state.user_mobile}`")
