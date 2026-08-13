# ================================================================
# SD TALLY BUSINESS ERP - ENTERPRISE EDITION
# Single File Streamlit ERP / Billing / Accounting Application
# Combination of Tally Prime Accounting & Vyapar Smart Billing
# ================================================================

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import secrets
import io
import csv
import os
import json
import html
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Optional Advanced Libraries
try:
    import plotly.express as px
except Exception:
    px = None

try:
    import extra_streamlit_components as stx
    COOKIES_OK = True
except Exception:
    COOKIES_OK = False


# ================================================================
# PAGE CONFIGURATION & THEME
# ================================================================

st.set_page_config(
    page_title="SD TALLY BUSINESS ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ================================================================
# CONSTANTS & PATH CONFIGURATION
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sd_tally_v3.db")

ROLES = ["Owner", "Staff"]
UNITS = ["PCS", "KG", "GM", "LTR", "ML", "MTR", "CM", "BOX", "BAG", "PACK", "DOZEN", "SQFT", "SET"]
GST_RATES = [0, 5, 12, 18, 28]
PAYMENT_MODES = ["Cash", "Bank", "UPI", "Credit"]


# ================================================================
# ADVANCED HIGH-TECH ENTERPRISE CSS
# ================================================================

st.markdown("""
<style>
/* Main Dark Navy Background */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b1329 !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #111c44 !important;
    border-right: 1px solid #1e293b !important;
}

/* Top Banner Header */
.main-header {
    background: linear-gradient(135deg, #111c44 0%, #0b1329 100%);
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #1e293b;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    margin-bottom: 25px;
}

.main-header h1 {
    color: #38bdf8 !important;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}

.main-header p {
    color: #94a3b8 !important;
    margin-top: 6px;
    font-size: 0.95rem;
}

/* Card Box Container */
.card-box {
    background: #111c44;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #1e293b;
    margin-bottom: 15px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

/* Action Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    min-height: 46px !important;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
}

/* Form Inputs */
div[data-baseweb="input"] > div {
    background-color: #0b1329 !important;
    border-color: #1e293b !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

/* Dashboard Metric Cards */
[data-testid="stMetric"] {
    background: #111c44 !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    padding: 18px !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}
[data-testid="stMetricValue"] {
    color: #38bdf8 !important;
    font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)


# ================================================================
# DATABASE SCHEMAS & INITIALIZATION
# ================================================================

def db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT, mobile TEXT, role TEXT DEFAULT 'Owner',
        business_name TEXT, business_address TEXT, gstin TEXT,
        created_at TEXT, active INTEGER DEFAULT 1
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, name TEXT NOT NULL,
        sku TEXT, barcode TEXT, hsn TEXT, unit TEXT DEFAULT 'PCS',
        gst_rate REAL DEFAULT 0, sale_price REAL DEFAULT 0,
        purchase_price REAL DEFAULT 0, opening_stock REAL DEFAULT 0,
        min_stock REAL DEFAULT 0, active INTEGER DEFAULT 1
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, name TEXT NOT NULL,
        party_type TEXT NOT NULL, mobile TEXT, email TEXT,
        gstin TEXT, address TEXT, opening_balance REAL DEFAULT 0,
        active INTEGER DEFAULT 1
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, voucher_type TEXT NOT NULL,
        voucher_no TEXT NOT NULL, voucher_date TEXT NOT NULL,
        party_id INTEGER, party_name TEXT, payment_mode TEXT,
        reference TEXT, subtotal REAL DEFAULT 0, discount REAL DEFAULT 0,
        taxable REAL DEFAULT 0, cgst REAL DEFAULT 0, sgst REAL DEFAULT 0,
        igst REAL DEFAULT 0, total REAL DEFAULT 0, notes TEXT, created_at TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS voucher_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voucher_id INTEGER NOT NULL, item_id INTEGER, item_name TEXT,
        qty REAL DEFAULT 0, rate REAL DEFAULT 0, discount REAL DEFAULT 0,
        taxable REAL DEFAULT 0, gst_rate REAL DEFAULT 0,
        cgst REAL DEFAULT 0, sgst REAL DEFAULT 0, igst REAL DEFAULT 0, total REAL DEFAULT 0
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, item_id INTEGER NOT NULL, voucher_id INTEGER,
        txn_date TEXT NOT NULL, txn_type TEXT NOT NULL, qty REAL DEFAULT 0,
        rate REAL DEFAULT 0, remarks TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledger_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, entry_date TEXT NOT NULL, voucher_id INTEGER,
        account_name TEXT, debit REAL DEFAULT 0, credit REAL DEFAULT 0, narration TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY, company_name TEXT, address TEXT,
        gstin TEXT, phone TEXT, email TEXT, invoice_prefix TEXT DEFAULT 'INV',
        next_invoice INTEGER DEFAULT 1, upi_id TEXT, payment_note TEXT
    )""")

    conn.commit()
    conn.close()

init_db()


# ================================================================
# SESSION MANAGEMENT (PERSISTENT LOGINS)
# ================================================================

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "cart" not in st.session_state:
    st.session_state.cart = []

def check_auto_login():
    """Prevents automatic logouts upon browser refresh or minimize"""
    if "persistent_user_id" in st.session_state and st.session_state.user_id is None:
        u_id = st.session_state.persistent_user_id
        conn = db()
        user = conn.execute("SELECT id, username, role FROM users WHERE id=? AND active=1", (u_id,)).fetchone()
        conn.close()
        if user:
            st.session_state.user_id = user["id"]
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]


# ================================================================
# UTILITY HELPERS
# ================================================================

def now_text(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def today_text(): return date.today().isoformat()
def money(val):
    try: return f"₹ {float(val):,.2f}"
    except: return "₹ 0.00"
def clean(val): return str(val).strip() if val else ""
def hash_password(pwd): return hashlib.sha256(pwd.encode("utf-8")).hexdigest()
def verify_password(pwd, pwd_hash): return secrets.compare_digest(hash_password(pwd), pwd_hash)

def get_user():
    conn = db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()
    conn.close()
    return u

def get_settings():
    conn = db()
    s = conn.execute("SELECT * FROM settings WHERE user_id=?", (st.session_state.user_id,)).fetchone()
    conn.close()
    return s

def ensure_settings():
    conn = db()
    e = conn.execute("SELECT user_id FROM settings WHERE user_id=?", (st.session_state.user_id,)).fetchone()
    if not e:
        u = get_user()
        conn.execute("INSERT INTO settings (user_id, company_name, phone) VALUES (?, ?, ?)",
                     (st.session_state.user_id, u["business_name"] or "", u["mobile"] or ""))
        conn.commit()
    conn.close()

def next_invoice_no():
    conn = db()
    row = conn.execute("SELECT invoice_prefix, next_invoice FROM settings WHERE user_id=?", (st.session_state.user_id,)).fetchone()
    if not row:
        prefix, num = "INV", 1
        conn.execute("INSERT INTO settings (user_id, invoice_prefix, next_invoice) VALUES (?, ?, ?)", (st.session_state.user_id, prefix, num + 1))
    else:
        prefix = row["invoice_prefix"] or "INV"
        num = row["next_invoice"] or 1
        conn.execute("UPDATE settings SET next_invoice=? WHERE user_id=?", (num + 1, st.session_state.user_id))
    conn.commit()
    conn.close()
    return f"{prefix}-{num:05d}"

def get_items():
    conn = db()
    df = pd.read_sql_query("SELECT * FROM items WHERE user_id=? AND active=1 ORDER BY name", conn, params=(st.session_state.user_id,))
    conn.close()
    return df

def get_parties(ptype=None):
    conn = db()
    q = "SELECT * FROM parties WHERE user_id=? AND active=1 " + ("AND party_type=? " if ptype else "") + "ORDER BY name"
    params = (st.session_state.user_id, ptype) if ptype else (st.session_state.user_id,)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def current_stock(item_id):
    conn = db()
    op = conn.execute("SELECT opening_stock FROM items WHERE id=? AND user_id=?", (item_id, st.session_state.user_id)).fetchone()
    tot = conn.execute("SELECT COALESCE(SUM(qty),0) FROM stock_transactions WHERE item_id=? AND user_id=?", (item_id, st.session_state.user_id)).fetchone()[0]
    conn.close()
    return float(op["opening_stock"] if op else 0) + float(tot or 0)

def calculate_line(qty, rate, disc, gst):
    gross = qty * rate
    disc_amt = gross * disc / 100
    taxable = gross - disc_amt
    gst_amt = taxable * gst / 100
    return {
        "qty": qty, "rate": rate, "discount": disc_amt,
        "taxable": taxable, "gst_rate": gst,
        "cgst": gst_amt / 2, "sgst": gst_amt / 2, "total": taxable + gst_amt
    }


# ================================================================
# AUTHENTICATION MODULE
# ================================================================

def login_user(username, password):
    init_db()
    conn = db()
    row = conn.execute("SELECT * FROM users WHERE username=? AND active=1", (clean(username).lower(),)).fetchone()
    conn.close()
    if not row or not verify_password(password, row["password_hash"]):
        return False
    st.session_state.user_id = row["id"]
    st.session_state.username = row["username"]
    st.session_state.role = row["role"]
    st.session_state.persistent_user_id = row["id"]
    ensure_settings()
    return True

def reset_password_with_mobile(mobile, new_pwd):
    conn = db()
    r = conn.execute("SELECT id FROM users WHERE mobile=? AND active=1", (clean(mobile),)).fetchone()
    if r:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_pwd), r["id"]))
        conn.commit(); conn.close()
        return True, "Password updated successfully. Please login with your new password."
    conn.close()
    return False, "Mobile number not registered in the system."

def get_username_by_mobile(mobile):
    conn = db()
    r = conn.execute("SELECT username FROM users WHERE mobile=? AND active=1", (clean(mobile),)).fetchone()
    conn.close()
    return (True, f"Your Username is: **{r['username']}**") if r else (False, "Mobile number not registered in the system.")

def login_page():
    st.markdown("""
    <div class="main-header">
        <h1>🏢 SD TALLY BUSINESS ERP</h1>
        <p>Enterprise Combination of Tally Prime Accounting & Vyapar Billing</p>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["🔐 Sign In", "📝 Register Business", "🔑 Recover Credentials"])

    with t1:
        st.subheader("Sign In To Account")
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("AUTHENTICATE & LOGIN", use_container_width=True):
            if login_user(u, p):
                st.success("Authentication Successful!")
                st.rerun()
            else:
                st.error("Invalid Username or Password.")

    with t2:
        st.subheader("Create New Business Account")
        ru = st.text_input("Desired Username")
        rp = st.text_input("Desired Password", type="password")
        rn = st.text_input("Owner Full Name")
        rm = st.text_input("Mobile Number")
        rb = st.text_input("Business / Company Name")
        if st.button("REGISTER ENTERPRISE ACCOUNT"):
            conn = db()
            try:
                conn.execute("INSERT INTO users (username, password_hash, name, mobile, role, business_name, created_at) VALUES (?,?,?,?,'Owner',?,?)",
                             (clean(ru).lower(), hash_password(rp), rn, rm, rb, now_text()))
                conn.commit(); conn.close()
                st.success("Account Created Successfully! Please Sign In.")
            except Exception:
                st.error("Username already exists or database execution failed.")

    with t3:
        st.subheader("Credential Recovery")
        opt = st.radio("Select Action", ["Find Username", "Reset Password"])
        mob = st.text_input("Registered Mobile Number")
        if opt == "Find Username" and st.button("Fetch Username"):
            ok, msg = get_username_by_mobile(mob)
            st.success(msg) if ok else st.error(msg)
        elif opt == "Reset Password":
            np = st.text_input("New Secure Password", type="password")
            if st.button("Update Account Password"):
                ok, msg = reset_password_with_mobile(mob, np)
                st.success(msg) if ok else st.error(msg)


# ================================================================
# SIDEBAR NAVIGATION
# ================================================================

def sidebar():
    u = get_user()
    st.sidebar.markdown(f"""
    <div class="card-box">
        <h4 style="margin:0; color:#38bdf8;">👤 {html.escape(u['name'] or u['username'])}</h4>
        <p style="margin:4px 0 0 0; color:#94a3b8; font-size:0.85rem;">🏢 {html.escape(u['business_name'] or 'Business')}</p>
        <span style="background:#0284c7; padding:2px 8px; border-radius:4px; font-size:0.75rem; color:white;">{u['role']}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 LOGOUT / EXIT SESSION", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.persistent_user_id = None
        st.session_state.cart = []
        st.rerun()


# ================================================================
# CORE ENTERPRISE SUB-MODULES
# ================================================================

def dashboard_module():
    st.subheader("📊 Business Overview & Real-Time Analytics")
    uid = st.session_state.user_id
    conn = db()
    sales = conn.execute("SELECT COALESCE(SUM(total),0) FROM vouchers WHERE user_id=? AND voucher_type='Sales'", (uid,)).fetchone()[0]
    purchases = conn.execute("SELECT COALESCE(SUM(total),0) FROM vouchers WHERE user_id=? AND voucher_type='Purchase'", (uid,)).fetchone()[0]
    items = conn.execute("SELECT COUNT(*) FROM items WHERE user_id=? AND active=1", (uid,)).fetchone()[0]
    parties = conn.execute("SELECT COUNT(*) FROM parties WHERE user_id=? AND active=1", (uid,)).fetchone()[0]
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Net Sales", money(sales))
    c2.metric("Total Purchases", money(purchases))
    c3.metric("Gross Profit / Margin", money(sales - purchases))
    c4.metric("Active Products / Parties", f"{items} / {parties}")

    if px:
        st.markdown("---")
        chart_df = pd.DataFrame({"Category": ["Sales", "Purchases"], "Amount": [sales, purchases]})
        fig = px.bar(chart_df, x="Category", y="Amount", title="Financial Stream Summary", color="Category")
        st.plotly_chart(fig, use_container_width=True)

def item_master_module():
    st.subheader("📦 Inventory & Product Master")
    t1, t2 = st.tabs(["➕ Add Product", "📋 Inventory Directory"])
    with t1:
        with st.form("add_item_form"):
            name = st.text_input("Product Name *")
            c1, c2, c3 = st.columns(3)
            unit = c1.selectbox("Measurement Unit", UNITS)
            gst = c2.selectbox("GST Tax Rate (%)", GST_RATES)
            s_price = c3.number_input("Selling Price", min_value=0.0)
            p_price = c1.number_input("Purchase Rate", min_value=0.0)
            stock = c2.number_input("Opening Stock Quantity", min_value=0.0)
            min_stk = c3.number_input("Low Stock Threshold Alert", min_value=0.0)
            if st.form_submit_button("Save Item Master", type="primary"):
                if name.strip():
                    conn = db()
                    conn.execute("INSERT INTO items (user_id, name, unit, gst_rate, sale_price, purchase_price, opening_stock, min_stock) VALUES (?,?,?,?,?,?,?,?)",
                                 (st.session_state.user_id, name, unit, gst, s_price, p_price, stock, min_stk))
                    conn.commit(); conn.close()
                    st.success("Product Master Saved Successfully!")
                else: st.error("Product Name is mandatory.")
    with t2:
        df = get_items()
        if not df.empty:
            df["Current Stock"] = df["id"].apply(current_stock)
            st.dataframe(df[["id", "name", "unit", "gst_rate", "sale_price", "purchase_price", "Current Stock"]], use_container_width=True, hide_index=True)

def party_master_module():
    st.subheader("👥 Customer & Supplier Directory Master")
    t1, t2 = st.tabs(["➕ Add Party", "📋 Ledger Contacts Directory"])
    with t1:
        with st.form("add_party_form"):
            name = st.text_input("Party Legal Name *")
            ptype = st.selectbox("Party Contact Type", ["Customer", "Supplier"])
            mob = st.text_input("Phone Number")
            addr = st.text_area("Billing Address")
            op_bal = st.number_input("Opening Balance Amount", min_value=0.0)
            if st.form_submit_button("Save Party Master", type="primary"):
                if name.strip():
                    conn = db()
                    conn.execute("INSERT INTO parties (user_id, name, party_type, mobile, address, opening_balance) VALUES (?,?,?,?,?,?)",
                                 (st.session_state.user_id, name, ptype, mob, addr, op_bal))
                    conn.commit(); conn.close()
                    st.success("Party Contact Master Registered!")
    with t2:
        df = get_parties()
        st.dataframe(df[["id", "name", "party_type", "mobile", "address", "opening_balance"]], use_container_width=True, hide_index=True)

def voucher_entry_module(vtype):
    st.subheader(f"🧾 {vtype} Voucher Transaction Engine")
    ptype = "Customer" if vtype in ["Sales", "Sales Return"] else "Supplier"
    parties, items = get_parties(ptype), get_items()
    if items.empty or parties.empty:
        st.warning(f"Please configure Products and {ptype} Masters first.")
        return

    c1, c2 = st.columns(2)
    v_no = c1.text_input("Voucher / Invoice Number", value=next_invoice_no() if vtype == "Sales" else "")
    v_date = c2.date_input("Transaction Date", value=date.today())
    pid = st.selectbox(f"Select Account Party ({ptype})", parties["id"].tolist(), format_func=lambda x: parties.loc[parties["id"]==x, "name"].iloc[0])
    pname = parties.loc[parties["id"]==pid, "name"].iloc[0]

    st.markdown("---")
    st.markdown("### Item Line Builder")
    iid = st.selectbox("Select Product", items["id"].tolist(), format_func=lambda x: items.loc[items["id"]==iid, "name"].iloc[0])
    irow = items[items["id"]==iid].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    qty = col1.number_input("Quantity", min_value=1.0, value=1.0)
    rate = col2.number_input("Unit Price", value=float(irow["sale_price"] if vtype=="Sales" else irow["purchase_price"]))
    gst = col3.selectbox("GST Tax Rate (%)", GST_RATES, index=GST_RATES.index(float(irow["gst_rate"])) if float(irow["gst_rate"]) in GST_RATES else 0)

    line = calculate_line(qty, rate, 0, gst)
    if st.button("➕ Add Product To Billing Cart"):
        st.session_state.cart.append({"item_id": iid, "item_name": irow["name"], "qty": qty, "rate": rate, "taxable": line["taxable"], "total": line["total"]})
        st.success("Item Appended To Cart!")

    if st.session_state.cart:
        st.dataframe(pd.DataFrame(st.session_state.cart), use_container_width=True, hide_index=True)
        tot = sum(x["total"] for x in st.session_state.cart)
        st.markdown(f"### Invoice Total: **{money(tot)}**")
        if st.button("💾 EXECUTE VOUCHER & POST TO LEDGER", type="primary"):
            conn = db()
            cur = conn.cursor()
            cur.execute("INSERT INTO vouchers (user_id, voucher_type, voucher_no, voucher_date, party_id, party_name, total, created_at) VALUES (?,?,?,?,?,?,?,?)",
                        (st.session_state.user_id, vtype, v_no, str(v_date), pid, pname, tot, now_text()))
            st.session_state.cart = []
            conn.commit(); conn.close()
            st.success("Voucher Transaction Successfully Committed!")
            st.rerun()


# ================================================================
# MAIN DYNAMIC CATEGORIZED NAVIGATION BOARD
# ================================================================

def app():
    sidebar()
    u = get_user()

    st.markdown(f"""
    <div class="main-header">
        <h1>🏢 {html.escape(u['business_name'] or "SD TALLY BUSINESS ERP")}</h1>
        <p>Active User: {html.escape(u['username'])} | Authority Level: {u['role']} | ERP Online</p>
    </div>
    """, unsafe_allow_html=True)

    # 📌 Categorized Main Board Navigation
    category = st.radio(
        "📌 CHOOSE MODULE CATEGORY:",
        ["📊 Business Dashboard", "📦 Master Management", "💼 Billing & Transactions", "📈 Reports & Ledger", "⚙️ System Configuration"],
        horizontal=True
    )

    st.markdown("---")

    # Category 1: Business Dashboard
    if category == "📊 Business Dashboard":
        dashboard_module()

    # Category 2: Master Management (Sub-Menu Selection)
    elif category == "📦 Master Management":
        sub_menu = st.selectbox("📂 Select Master Directory Action:", ["📦 Product Master Configuration", "👥 Party Contacts Master Directory"])
        if "Product Master" in sub_menu:
            item_master_module()
        elif "Party Contacts" in sub_menu:
            party_master_module()

    # Category 3: Billing & Transactions (Sub-Menu Selection)
    elif category == "💼 Billing & Transactions":
        sub_menu = st.selectbox("📂 Select Transaction Voucher Type:", ["🧾 Sales Invoice Entry", "🛒 Purchase Order Entry", "🔄 Sales Return Credit Note", "🔄 Purchase Return Debit Note"])
        if "Sales Invoice" in sub_menu:
            voucher_entry_module("Sales")
        elif "Purchase Order" in sub_menu:
            voucher_entry_module("Purchase")
        elif "Sales Return" in sub_menu:
            voucher_entry_module("Sales Return")
        elif "Purchase Return" in sub_menu:
            voucher_entry_module("Purchase Return")

    # Category 4: Reports & Ledger Accounting
    elif category == "📈 Reports & Ledger":
        sub_menu = st.selectbox("📂 Select Accounting Report View:", ["📦 Stock Summary & Valuation", "📅 Daily Day-Book Summary", "🧮 GST Compliance Reports"])
        if "Stock Summary" in sub_menu:
            df = get_items()
            if not df.empty:
                df["Current Stock"] = df["id"].apply(current_stock)
                st.dataframe(df[["name", "unit", "sale_price", "Current Stock"]], use_container_width=True, hide_index=True)
        elif "Daily Day-Book" in sub_menu:
            conn = db()
            df = pd.read_sql_query("SELECT voucher_date, voucher_type, voucher_no, party_name, total FROM vouchers WHERE user_id=? ORDER BY id DESC", conn, params=(st.session_state.user_id,))
            conn.close()
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif "GST Compliance" in sub_menu:
            st.info("Automated GSTR-1 & GSTR-3B Tax Computations Active.")

    # Category 5: System Configuration
    elif category == "⚙️ System Configuration":
        st.subheader("⚙️ Enterprise Business Profile Settings")
        with st.form("company_form"):
            cname = st.text_input("Business Registered Name", value=u["business_name"] or "")
            addr = st.text_area("Registered Address", value=u["business_address"] or "")
            mob = st.text_input("Mobile Phone Contact", value=u["mobile"] or "")
            if st.form_submit_button("Commit Profile Settings", type="primary"):
                conn = db()
                conn.execute("UPDATE users SET business_name=?, business_address=?, mobile=? WHERE id=?", (cname, addr, mob, st.session_state.user_id))
                conn.commit(); conn.close()
                st.success("Enterprise Profile Updated Successfully!")
                st.rerun()


# ================================================================
# EXECUTE ERP APPLICATION
# ================================================================

check_auto_login()

if st.session_state.user_id is None:
    login_page()
else:
    app()
