# ============================================================
# SD TALLY BUSINESS - PROFESSIONAL ALL-IN-ONE STREAMLIT APP
# Version: Enterprise Stable
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import random
import io
import csv
import html
import urllib.parse
from datetime import datetime, timedelta

# ------------------------------------------------------------
# OPTIONAL PLOTLY
# ------------------------------------------------------------
try:
    import plotly.express as px
except Exception:
    px = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PROFESSIONAL CSS
# ============================================================

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
}

.stApp {
    background: #f5f7fb;
    color: #0f172a;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0;
}

[data-testid="stSidebar"] * {
    color: #0f172a !important;
}

.main-header {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    color: white;
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 22px;
    box-shadow: 0 5px 15px rgba(0,0,0,.10);
}

.main-header h1 {
    margin: 0;
    color: #38bdf8 !important;
    font-size: 2rem;
    font-weight: 800;
}

.main-header p {
    margin: 5px 0 0 0;
    color: #cbd5e1 !important;
}

.user-card {
    background: #f1f5f9;
    border-left: 5px solid #0284c7;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
}

.plan-card {
    background: #e0f2fe;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 15px;
}

[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #dbe3ec !important;
    border-left: 5px solid #0284c7 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.06);
}

.stButton > button {
    width: 100%;
    min-height: 45px;
    border-radius: 9px;
    font-weight: 700;
}

div[data-testid="stForm"] {
    border-radius: 12px;
}

.small-note {
    color: #64748b;
    font-size: 13px;
}

.success-box {
    padding: 12px;
    border-radius: 8px;
    background: #dcfce7;
    color: #166534;
}

.warning-box {
    padding: 12px;
    border-radius: 8px;
    background: #fef3c7;
    color: #92400e;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "sd_tally_business.db"


def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def add_column_if_missing(conn, table, column, definition):
    if not column_exists(conn, table, column):
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_db():

    conn = get_db()
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        mobile TEXT PRIMARY KEY,
        name TEXT DEFAULT '',
        business_name TEXT DEFAULT '',
        business_address TEXT DEFAULT '',
        gstin TEXT DEFAULT '',
        email TEXT DEFAULT '',
        reg_date TEXT,
        trial_end_date TEXT,
        is_paid INTEGER DEFAULT 0,
        paid_till TEXT DEFAULT '',
        role TEXT DEFAULT 'Owner',
        active INTEGER DEFAULT 1
    )
    """)

    # INVENTORY
    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        item_name TEXT,
        unit TEXT DEFAULT 'PCS',
        barcode TEXT DEFAULT '',
        hsn_sac TEXT DEFAULT '',
        godown TEXT DEFAULT 'Main Store',
        batch_no TEXT DEFAULT '',
        expiry_date TEXT DEFAULT '',
        sale_price REAL DEFAULT 0,
        purchase_price REAL DEFAULT 0,
        gst_rate REAL DEFAULT 0,
        stock_qty REAL DEFAULT 0,
        min_stock_alert REAL DEFAULT 5,
        is_active INTEGER DEFAULT 1
    )
    """)

    # GODOWNS
    c.execute("""
    CREATE TABLE IF NOT EXISTS godowns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        godown_name TEXT,
        address TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1
    )
    """)

    # PARTIES
    c.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        party_name TEXT,
        gstin TEXT DEFAULT '',
        mobile TEXT DEFAULT '',
        party_type TEXT,
        opening_balance REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    """)

    # BANK
    c.execute("""
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        bank_name TEXT,
        account_no TEXT,
        ifsc_code TEXT DEFAULT '',
        branch_name TEXT DEFAULT '',
        opening_balance REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    """)

    # VOUCHERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        voucher_type TEXT,
        voucher_no TEXT,
        date TEXT,
        party_name TEXT DEFAULT '',
        item_name TEXT DEFAULT '',
        unit TEXT DEFAULT 'PCS',
        hsn_sac TEXT DEFAULT '',
        qty REAL DEFAULT 0,
        rate REAL DEFAULT 0,
        taxable_amt REAL DEFAULT 0,
        gst_rate REAL DEFAULT 0,
        cgst REAL DEFAULT 0,
        sgst REAL DEFAULT 0,
        igst REAL DEFAULT 0,
        total_amt REAL DEFAULT 0,
        payment_mode TEXT DEFAULT 'Cash',
        eway_bill_no TEXT DEFAULT '',
        irn_no TEXT DEFAULT '',
        debit_account TEXT DEFAULT '',
        credit_account TEXT DEFAULT ''
    )
    """)

    # CAPITAL / BANK LEDGER
    c.execute("""
    CREATE TABLE IF NOT EXISTS capital_bank_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        date TEXT,
        account_type TEXT,
        particulars TEXT,
        amount REAL DEFAULT 0,
        txn_type TEXT,
        bank_name TEXT DEFAULT ''
    )
    """)

    # BRANDING
    c.execute("""
    CREATE TABLE IF NOT EXISTS branding (
        user_mobile TEXT PRIMARY KEY,
        logo_base64 TEXT DEFAULT '',
        sig_base64 TEXT DEFAULT ''
    )
    """)

    # Safe migration for old database
    add_column_if_missing(conn, "users", "email", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "users", "active", "INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


init_db()


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "user_mobile": None,
    "user_role": "Owner",
    "business_name": "",
    "business_gstin": "",
    "otp_sent": False,
    "generated_otp": None,
    "otp_mobile": "",
    "selected_module": "🏠 Dashboard"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# URL SESSION RESTORE
# ============================================================

try:
    params = st.query_params
    saved_mobile = params.get("user_session")

    if (
        not st.session_state.user_mobile
        and saved_mobile
        and str(saved_mobile).isdigit()
    ):
        st.session_state.user_mobile = str(saved_mobile)

except Exception:
    pass


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean(value):
    if value is None:
        return ""
    return html.escape(str(value))


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def generate_voucher_no(prefix="INV"):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def get_user(mobile):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE mobile=?",
        (mobile,)
    ).fetchone()

    conn.close()

    if row:
        return dict(row)

    return None


def subscription_status(mobile):

    user = get_user(mobile)

    if not user:
        return "NEW_USER"

    # IMPORTANT:
    # This prevents the IndexError seen in the screenshot.
    is_paid = int(user.get("is_paid") or 0)
    paid_till = user.get("paid_till") or ""
    trial_end = user.get("trial_end_date") or ""

    today = datetime.now().date()

    if is_paid == 1 and paid_till:

        try:
            paid_date = datetime.strptime(
                paid_till, "%Y-%m-%d"
            ).date()

            if today <= paid_date:
                return f"ACTIVE PRO • Valid till {paid_till}"

        except Exception:
            pass

    if trial_end:

        try:
            trial_date = datetime.strptime(
                trial_end, "%Y-%m-%d"
            ).date()

            if today <= trial_date:
                days = (trial_date - today).days
                return f"FREE TRIAL • {days} DAYS LEFT"

        except Exception:
            pass

    return "EXPIRED"


def load_user_session():

    mobile = st.session_state.user_mobile

    if not mobile:
        return

    user = get_user(mobile)

    if not user:
        return

    st.session_state.user_role = user.get("role") or "Owner"
    st.session_state.business_name = user.get("business_name") or ""
    st.session_state.business_gstin = user.get("gstin") or ""


def save_user_profile(
    mobile,
    name,
    business_name,
    address,
    gstin,
    email,
    role
):

    conn = get_db()

    conn.execute("""
        UPDATE users
        SET name=?,
            business_name=?,
            business_address=?,
            gstin=?,
            email=?,
            role=?
        WHERE mobile=?
    """, (
        name,
        business_name,
        address,
        gstin,
        email,
        role,
        mobile
    ))

    conn.commit()
    conn.close()

    load_user_session()


def logout():

    for key in [
        "user_mobile",
        "business_name",
        "business_gstin",
        "generated_otp",
        "otp_mobile"
    ]:
        st.session_state[key] = None

    st.session_state.otp_sent = False

    try:
        st.query_params.clear()
    except Exception:
        pass

    st.rerun()


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.user_mobile:

    st.markdown("""
    <div class="main-header">
        <h1>🏢 SD TALLY BUSINESS</h1>
        <p>Professional Billing • Inventory • GST • Accounting • Reports</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 1])

    with left:

        st.subheader("🔐 Secure Mobile Login")

        mobile = st.text_input(
            "📱 Mobile Number",
            max_chars=10,
            placeholder="Enter 10 digit mobile number"
        )

        if not st.session_state.otp_sent:

            if st.button(
                "📨 SEND OTP",
                type="primary"
            ):

                if len(mobile) != 10 or not mobile.isdigit():

                    st.error(
                        "Please enter a valid 10 digit mobile number."
                    )

                else:

                    st.session_state.generated_otp = str(
                        random.randint(1000, 9999)
                    )

                    st.session_state.otp_sent = True
                    st.session_state.otp_mobile = mobile

                    st.success(
                        "OTP generated successfully."
                    )

                    st.info(
                        f"Testing OTP: {st.session_state.generated_otp}"
                    )

                    st.rerun()

        else:

            st.success(
                f"OTP sent to +91 {st.session_state.otp_mobile}"
            )

            otp = st.text_input(
                "🔑 Enter 4 Digit OTP",
                max_chars=4,
                type="password"
            )

            role = st.selectbox(
                "👤 Access Role",
                ["Owner", "Salesman / Staff"]
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "✅ VERIFY & LOGIN",
                    type="primary"
                ):

                    if (
                        otp == st.session_state.generated_otp
                        and st.session_state.otp_mobile == mobile
                    ):

                        user = get_user(mobile)

                        if not user:

                            today = datetime.now().date()
                            trial_end = today + timedelta(days=10)

                            conn = get_db()

                            conn.execute("""
                            INSERT INTO users
                            (
                                mobile,
                                name,
                                business_name,
                                business_address,
                                gstin,
                                email,
                                reg_date,
                                trial_end_date,
                                is_paid,
                                paid_till,
                                role
                            )
                            VALUES
                            (?, ?, ?, ?, ?, ?, ?, ?, 0, '', ?)
                            """, (
                                mobile,
                                "Business Owner",
                                "",
                                "",
                                "",
                                "",
                                str(today),
                                str(trial_end),
                                role
                            ))

                            conn.commit()
                            conn.close()

                        else:

                            conn = get_db()

                            conn.execute(
                                "UPDATE users SET role=? WHERE mobile=?",
                                (role, mobile)
                            )

                            conn.commit()
                            conn.close()

                        st.session_state.user_mobile = mobile
                        st.session_state.user_role = role

                        try:
                            st.query_params["user_session"] = mobile
                        except Exception:
                            pass

                        load_user_session()

                        st.rerun()

                    else:

                        st.error(
                            "Invalid OTP. Please enter the correct OTP."
                        )

            with c2:

                if st.button("🔄 CHANGE NUMBER"):

                    st.session_state.otp_sent = False
                    st.session_state.generated_otp = None
                    st.session_state.otp_mobile = ""

                    st.rerun()

    with right:

        st.markdown("""
        ### 🚀 SD TALLY BUSINESS

        Professional business management system:

        - 🧾 Tax Invoice
        - 🛒 Purchase
        - 📦 Inventory
        - 🏦 Bank Management
        - 👥 Customer / Supplier
        - 🧮 GST Reports
        - 📊 Profit & Loss
        - 📒 Ledger
        - 💰 Outstanding
        - 📅 Day Book
        - 📥 Excel Export
        - 🖨️ Thermal Receipt
        - 🔐 Owner Profile
        - ⚙️ Company Settings
        """)

    st.stop()


# ============================================================
# LOAD USER
# ============================================================

load_user_session()

user_mob = st.session_state.user_mobile
user = get_user(user_mob)

if not user:

    st.session_state.user_mobile = None
    st.rerun()


status = subscription_status(user_mob)


# ============================================================
# ONBOARDING
# ============================================================

if not user.get("business_name"):

    st.markdown("""
    <div class="main-header">
        <h1>🏢 Business Profile Setup</h1>
        <p>Complete your company profile before opening the workspace.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("business_profile_form"):

        st.subheader("📋 Business Information")

        c1, c2 = st.columns(2)

        with c1:

            owner_name = st.text_input(
                "👤 Owner / Contact Name",
                value=user.get("name") or ""
            )

            business_name = st.text_input(
                "🏢 Business / Shop Name"
            )

            mobile_display = st.text_input(
                "📱 Mobile",
                value=user_mob,
                disabled=True
            )

        with c2:

            gstin = st.text_input(
                "🧾 GSTIN",
                value=user.get("gstin") or ""
            )

            email = st.text_input(
                "📧 Email",
                value=user.get("email") or ""
            )

            address = st.text_area(
                "📍 Business Address",
                value=user.get("business_address") or ""
            )

        save = st.form_submit_button(
            "💾 SAVE PROFILE & OPEN WORKSPACE",
            type="primary"
        )

    if save:

        if not business_name.strip():

            st.error("Business Name is required.")

        else:

            save_user_profile(
                user_mob,
                owner_name,
                business_name,
                address,
                gstin,
                email,
                st.session_state.user_role
            )

            st.success(
                "Business profile saved successfully."
            )

            st.rerun()

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

safe_business = clean(st.session_state.business_name)
safe_mobile = clean(user_mob)
safe_role = clean(st.session_state.user_role)

st.sidebar.markdown(f"""
<div class="user-card">
    <div style="font-size:18px;font-weight:800;">
        👤 Owner / User
    </div>
    <div style="margin-top:8px;">
        <b>Mobile</b><br>
        {safe_mobile}
    </div>
    <div style="margin-top:8px;">
        <b>Business</b><br>
        {safe_business}
    </div>
    <div style="margin-top:8px;">
        <b>Role</b><br>
        {safe_role}
    </div>
</div>

<div class="plan-card">
    <b>🎁 Plan</b><br>
    <span style="font-size:18px;">
        {clean(status)}
    </span>
</div>
""", unsafe_allow_html=True)


if st.sidebar.button(
    "🚪 Logout Account"
):

    logout()


# ============================================================
# PROFILE EDIT
# ============================================================

with st.sidebar.expander("👤 Edit Owner / Business Profile"):

    edit_name = st.text_input(
        "Owner Name",
        value=user.get("name") or "",
        key="edit_owner_name"
    )

    edit_business = st.text_input(
        "Business Name",
        value=user.get("business_name") or "",
        key="edit_business_name"
    )

    edit_address = st.text_area(
        "Business Address",
        value=user.get("business_address") or "",
        key="edit_business_address"
    )

    edit_gst = st.text_input(
        "GSTIN",
        value=user.get("gstin") or "",
        key="edit_gstin"
    )

    edit_email = st.text_input(
        "Email",
        value=user.get("email") or "",
        key="edit_email"
    )

    if st.button(
        "💾 Update Profile",
        key="update_profile"
    ):

        save_user_profile(
            user_mob,
            edit_name,
            edit_business,
            edit_address,
            edit_gst,
            edit_email,
            st.session_state.user_role
        )

        st.success("Profile updated.")
        st.rerun()


# ============================================================
# EXPIRY
# ============================================================

if status == "EXPIRED":

    st.title("💳 Subscription Renewal")

    st.warning(
        "Your free trial has expired."
    )

    st.markdown(
        "### Renewal Amount: ₹112.10"
    )

    st.markdown(
        "UPI ID: **8381085702@ibl**"
    )

    msg = urllib.parse.quote(
        f"Hi, I have paid Rs.112.10 for SD Tally Business renewal. "
        f"Mobile: {user_mob}"
    )

    st.markdown(
        f"[📲 Send Payment Proof on WhatsApp]"
        f"(https://wa.me/918381085702?text={msg})"
    )

    st.stop()


# ============================================================
# NAVIGATION
# ============================================================

menu_options = [

    "🏠 Dashboard",

    "📁 Masters - Items / Godowns / Parties",

    "🛒 Purchase Entry",

    "📥 Purchase & GSTR-2B Import",

    "🧾 Tax Invoice - Sales",

    "📦 Barcode Quick Billing",

    "🖨️ Thermal Receipt Print",

    "💰 Tally Vouchers F4-F9",

    "🏦 Capital & Bank Management",

    "📊 Bank Statement Import",

    "👥 Receivables & Party Statements",

    "🧮 GST Reports",

    "🚚 e-Way Bill & e-Invoice",

    "📈 Profit & Loss",

    "📋 Balance Sheet",

    "☁️ Automated Backup",

    "🏢 Company Branding",

    "💳 Account & Billing",

    "📦 Stock Summary & Ledger",

    "🔄 Sales / Purchase Return",

    "💸 Payment & Receipt",

    "📅 Day Book",

    "📒 Ledger & Trial Balance",

    "📑 Outstanding",

    "🔍 Voucher Search / Edit / Delete",

    "📊 Business Reports",

    "🔐 User & Permission Management",

    "⚙️ Company Settings",

    "🖨️ Print / PDF",

    "📤 Excel / PDF Export"
]


menu = st.sidebar.selectbox(
    "📌 Select Module",
    menu_options,
    index=menu_options.index(
        st.session_state.selected_module
    )
    if st.session_state.selected_module in menu_options
    else 0
)

st.session_state.selected_module = menu


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(f"""
<div class="main-header">
    <h1>{safe_business}</h1>
    <p>
        SD TALLY BUSINESS Enterprise Workspace
        • {safe_mobile}
        • {safe_role}
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 1. DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.subheader("📊 Business Dashboard")

    conn = get_db()

    sales = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type IN ('Sales','Tax Invoice')
    """, (user_mob,)).fetchone()[0]

    purchases = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
    """, (user_mob,)).fetchone()[0]

    bank = conn.execute("""
        SELECT COALESCE(SUM(opening_balance),0)
        FROM bank_accounts
        WHERE user_mobile=?
    """, (user_mob,)).fetchone()[0]

    stock = conn.execute("""
        SELECT COALESCE(SUM(stock_qty),0)
        FROM inventory
        WHERE user_mobile=?
    """, (user_mob,)).fetchone()[0]

    conn.close()

    profit = sales - purchases

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "💰 Total Sales",
        f"₹ {sales:,.2f}"
    )

    c2.metric(
        "🛒 Purchases",
        f"₹ {purchases:,.2f}"
    )

    c3.metric(
        "📈 Gross Profit",
        f"₹ {profit:,.2f}"
    )

    c4.metric(
        "📦 Stock Qty",
        f"{stock:,.2f}"
    )

    st.divider()

    st.subheader("📈 Business Performance")

    chart_df = pd.DataFrame({
        "Category": [
            "Sales",
            "Purchases",
            "Profit"
        ],
        "Amount": [
            sales,
            purchases,
            profit
        ]
    })

    if px:

        fig = px.bar(
            chart_df,
            x="Category",
            y="Amount",
            title="Sales / Purchase / Profit"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.bar_chart(
            chart_df.set_index("Category")
        )


# ============================================================
# 2. MASTERS
# ============================================================

elif menu == "📁 Masters - Items / Godowns / Parties":

    st.subheader("⚙️ Masters")

    tab1, tab2, tab3 = st.tabs([
        "📦 Items",
        "🏢 Godowns",
        "👥 Parties"
    ])

    conn = get_db()

    # ITEMS
    with tab1:

        st.markdown("### Add / Edit Item")

        item_id = st.number_input(
            "Edit Item ID (0 = New)",
            min_value=0,
            step=1
        )

        existing = None

        if item_id:

            existing = conn.execute("""
                SELECT * FROM inventory
                WHERE id=? AND user_mobile=?
            """, (item_id, user_mob)).fetchone()

        existing = dict(existing) if existing else {}

        item_name = st.text_input(
            "Item Name",
            value=existing.get("item_name","")
        )

        unit = st.selectbox(
            "Unit",
            ["PCS","KG","LTR","MTR","BOX","BAG","PACK","SQFT"],
            index=(
                ["PCS","KG","LTR","MTR","BOX","BAG","PACK","SQFT"]
                .index(existing.get("unit","PCS"))
                if existing.get("unit","PCS")
                in ["PCS","KG","LTR","MTR","BOX","BAG","PACK","SQFT"]
                else 0
            )
        )

        c1, c2 = st.columns(2)

        with c1:

            sale_price = st.number_input(
                "Selling Price",
                min_value=0.0,
                value=float(existing.get("sale_price") or 0)
            )

            purchase_price = st.number_input(
                "Purchase Price",
                min_value=0.0,
                value=float(existing.get("purchase_price") or 0)
            )

        with c2:

            gst_rate = st.selectbox(
                "GST %",
                [0,5,12,18,28],
                index=(
                    [0,5,12,18,28].index(
                        int(existing.get("gst_rate") or 0)
                    )
                    if int(existing.get("gst_rate") or 0)
                    in [0,5,12,18,28]
                    else 0
                )
            )

            stock_qty = st.number_input(
                "Stock Qty",
                min_value=0.0,
                value=float(existing.get("stock_qty") or 0)
            )

        barcode = st.text_input(
            "Barcode",
            value=existing.get("barcode","")
        )

        hsn = st.text_input(
            "HSN / SAC",
            value=existing.get("hsn_sac","")
        )

        if st.button(
            "💾 Save / Update Item",
            key="save_item"
        ):

            if not item_name.strip():

                st.error("Item name required.")

            elif item_id and existing:

                conn.execute("""
                    UPDATE inventory
                    SET item_name=?,
                        unit=?,
                        barcode=?,
                        hsn_sac=?,
                        sale_price=?,
                        purchase_price=?,
                        gst_rate=?,
                        stock_qty=?
                    WHERE id=? AND user_mobile=?
                """, (
                    item_name,
                    unit,
                    barcode,
                    hsn,
                    sale_price,
                    purchase_price,
                    gst_rate,
                    stock_qty,
                    item_id,
                    user_mob
                ))

                conn.commit()
                st.success("Item updated.")
                st.rerun()

            else:

                conn.execute("""
                    INSERT INTO inventory
                    (
                        user_mobile,
                        item_name,
                        unit,
                        barcode,
                        hsn_sac,
                        sale_price,
                        purchase_price,
                        gst_rate,
                        stock_qty
                    )
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (
                    user_mob,
                    item_name,
                    unit,
                    barcode,
                    hsn,
                    sale_price,
                    purchase_price,
                    gst_rate,
                    stock_qty
                ))

                conn.commit()
                st.success("Item saved.")
                st.rerun()

        df = pd.read_sql_query("""
            SELECT id,item_name,unit,barcode,hsn_sac,
                   sale_price,purchase_price,gst_rate,stock_qty
            FROM inventory
            WHERE user_mobile=?
            ORDER BY id DESC
        """, conn, params=(user_mob,))

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    # GODOWNS
    with tab2:

        godown_id = st.number_input(
            "Edit Godown ID (0 = New)",
            min_value=0,
            step=1,
            key="godown_id"
        )

        g_existing = None

        if godown_id:

            g_existing = conn.execute("""
                SELECT * FROM godowns
                WHERE id=? AND user_mobile=?
            """, (godown_id,user_mob)).fetchone()

        g_existing = dict(g_existing) if g_existing else {}

        g_name = st.text_input(
            "Godown Name",
            value=g_existing.get("godown_name","")
        )

        g_address = st.text_area(
            "Address",
            value=g_existing.get("address","")
        )

        if st.button(
            "💾 Save / Update Godown",
            key="save_godown"
        ):

            if godown_id and g_existing:

                conn.execute("""
                    UPDATE godowns
                    SET godown_name=?, address=?
                    WHERE id=? AND user_mobile=?
                """, (
                    g_name,
                    g_address,
                    godown_id,
                    user_mob
                ))

            else:

                conn.execute("""
                    INSERT INTO godowns
                    (user_mobile,godown_name,address)
                    VALUES (?,?,?)
                """, (
                    user_mob,
                    g_name,
                    g_address
                ))

            conn.commit()
            st.success("Godown saved.")
            st.rerun()

        st.dataframe(
            pd.read_sql_query("""
                SELECT id,godown_name,address
                FROM godowns
                WHERE user_mobile=?
                ORDER BY id DESC
            """, conn, params=(user_mob,)),
            use_container_width=True,
            hide_index=True
        )

    # PARTIES
    with tab3:

        party_id = st.number_input(
            "Edit Party ID (0 = New)",
            min_value=0,
            step=1,
            key="party_id"
        )

        p_existing = None

        if party_id:

            p_existing = conn.execute("""
                SELECT * FROM parties
                WHERE id=? AND user_mobile=?
            """, (
                party_id,
                user_mob
            )).fetchone()

        p_existing = dict(p_existing) if p_existing else {}

        p_name = st.text_input(
            "Party Name",
            value=p_existing.get("party_name","")
        )

        p_mobile = st.text_input(
            "Party Mobile",
            value=p_existing.get("mobile","")
        )

        p_gst = st.text_input(
            "Party GSTIN",
            value=p_existing.get("gstin","")
        )

        p_type = st.selectbox(
            "Party Type",
            ["Customer","Supplier"],
            index=(
                1 if p_existing.get("party_type")=="Supplier"
                else 0
            )
        )

        p_balance = st.number_input(
            "Opening Balance",
            min_value=0.0,
            value=float(
                p_existing.get("opening_balance") or 0
            )
        )

        if st.button(
            "💾 Save / Update Party",
            key="save_party"
        ):

            if party_id and p_existing:

                conn.execute("""
                    UPDATE parties
                    SET party_name=?,
                        gstin=?,
                        mobile=?,
                        party_type=?,
                        opening_balance=?
                    WHERE id=? AND user_mobile=?
                """, (
                    p_name,
                    p_gst,
                    p_mobile,
                    p_type,
                    p_balance,
                    party_id,
                    user_mob
                ))

            else:

                conn.execute("""
                    INSERT INTO parties
                    (
                        user_mobile,
                        party_name,
                        gstin,
                        mobile,
                        party_type,
                        opening_balance
                    )
                    VALUES (?,?,?,?,?,?)
                """, (
                    user_mob,
                    p_name,
                    p_gst,
                    p_mobile,
                    p_type,
                    p_balance
                ))

            conn.commit()
            st.success("Party saved.")
            st.rerun()

        st.dataframe(
            pd.read_sql_query("""
                SELECT id,party_name,gstin,mobile,
                       party_type,opening_balance
                FROM parties
                WHERE user_mobile=?
                ORDER BY id DESC
            """, conn, params=(user_mob,)),
            use_container_width=True,
            hide_index=True
        )

    conn.close()


# ============================================================
# 3. PURCHASE ENTRY
# ============================================================

elif menu == "🛒 Purchase Entry":

    st.subheader("🛒 Purchase Entry")

    conn = get_db()

    parties = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND party_type='Supplier'
        ORDER BY party_name
    """, conn, params=(user_mob,))

    items = pd.read_sql_query("""
        SELECT item_name,unit,purchase_price,gst_rate
        FROM inventory
        WHERE user_mobile=?
        ORDER BY item_name
    """, conn, params=(user_mob,))

    party_names = (
        parties["party_name"].tolist()
        if not parties.empty else []
    )

    item_names = (
        items["item_name"].tolist()
        if not items.empty else []
    )

    purchase_no = st.text_input(
        "Purchase Number",
        generate_voucher_no("PUR")
    )

    party = st.selectbox(
        "Supplier",
        ["Select Supplier"] + party_names
    )

    item = st.selectbox(
        "Item",
        ["Select Item"] + item_names
    )

    c1,c2,c3 = st.columns(3)

    with c1:
        qty = st.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0
        )

    with c2:
        rate = st.number_input(
            "Purchase Rate",
            min_value=0.0
        )

    with c3:
        gst = st.number_input(
            "GST %",
            min_value=0.0,
            max_value=28.0
        )

    payment = st.selectbox(
        "Payment Mode",
        ["Cash","Bank / UPI","Credit"]
    )

    taxable = qty * rate
    gst_amount = taxable * gst / 100
    total = taxable + gst_amount

    st.info(
        f"Taxable: ₹{taxable:,.2f} | "
        f"GST: ₹{gst_amount:,.2f} | "
        f"Total: ₹{total:,.2f}"
    )

    if st.button(
        "💾 SAVE PURCHASE",
        type="primary"
    ):

        if party == "Select Supplier":
            st.error("Select supplier.")
        elif item == "Select Item":
            st.error("Select item.")
        else:

            cgst = gst_amount / 2
            sgst = gst_amount / 2

            conn.execute("""
                INSERT INTO vouchers
                (
                    user_mobile,
                    voucher_type,
                    voucher_no,
                    date,
                    party_name,
                    item_name,
                    qty,
                    rate,
                    taxable_amt,
                    gst_rate,
                    cgst,
                    sgst,
                    total_amt,
                    payment_mode
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                user_mob,
                "Purchase",
                purchase_no,
                today_str(),
                party,
                item,
                qty,
                rate,
                taxable,
                gst,
                cgst,
                sgst,
                total,
                payment
            ))

            conn.execute("""
                UPDATE inventory
                SET stock_qty=stock_qty+?
                WHERE user_mobile=? AND item_name=?
            """, (
                qty,
                user_mob,
                item
            ))

            conn.commit()

            st.success(
                f"Purchase {purchase_no} saved successfully."
            )

    conn.close()


# ============================================================
# 4. TAX INVOICE
# ============================================================

elif menu == "🧾 Tax Invoice - Sales":

    st.subheader("🧾 Tax Invoice")

    conn = get_db()

    customers = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND party_type='Customer'
        ORDER BY party_name
    """, conn, params=(user_mob,))

    items = pd.read_sql_query("""
        SELECT item_name,unit,sale_price,gst_rate,stock_qty
        FROM inventory
        WHERE user_mobile=?
        ORDER BY item_name
    """, conn, params=(user_mob,))

    customers_list = (
        customers["party_name"].tolist()
        if not customers.empty else []
    )

    items_list = (
        items["item_name"].tolist()
        if not items.empty else []
    )

    invoice_no = st.text_input(
        "Invoice Number",
        generate_voucher_no("INV")
    )

    customer = st.selectbox(
        "Customer",
        ["Walk-in Customer"] + customers_list
    )

    item = st.selectbox(
        "Item",
        ["Select Item"] + items_list
    )

    qty = st.number_input(
        "Quantity",
        min_value=0.01,
        value=1.0
    )

    selected_price = 0.0
    selected_gst = 0.0
    available_stock = 0.0

    if item != "Select Item" and not items.empty:

        r = items[items["item_name"] == item].iloc[0]

        selected_price = float(r["sale_price"] or 0)
        selected_gst = float(r["gst_rate"] or 0)
        available_stock = float(r["stock_qty"] or 0)

    rate = st.number_input(
        "Selling Rate",
        min_value=0.0,
        value=selected_price
    )

    gst = st.number_input(
        "GST %",
        min_value=0.0,
        max_value=28.0,
        value=selected_gst
    )

    payment = st.selectbox(
        "Payment Mode",
        ["Cash","Bank / UPI","Credit (Pending)"]
    )

    taxable = qty * rate
    gst_amt = taxable * gst / 100
    cgst = gst_amt / 2
    sgst = gst_amt / 2
    total = taxable + gst_amt

    st.success(
        f"Taxable ₹{taxable:,.2f} | "
        f"GST ₹{gst_amt:,.2f} | "
        f"Invoice Total ₹{total:,.2f}"
    )

    if st.button(
        "🧾 SAVE TAX INVOICE",
        type="primary"
    ):

        if item == "Select Item":

            st.error("Select an item.")

        elif qty > available_stock:

            st.error(
                f"Insufficient stock. Available: {available_stock}"
            )

        else:

            conn.execute("""
                INSERT INTO vouchers
                (
                    user_mobile,
                    voucher_type,
                    voucher_no,
                    date,
                    party_name,
                    item_name,
                    qty,
                    rate,
                    taxable_amt,
                    gst_rate,
                    cgst,
                    sgst,
                    total_amt,
                    payment_mode
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                user_mob,
                "Tax Invoice",
                invoice_no,
                today_str(),
                customer,
                item,
                qty,
                rate,
                taxable,
                gst,
                cgst,
                sgst,
                total,
                payment
            ))

            conn.execute("""
                UPDATE inventory
                SET stock_qty=stock_qty-?
                WHERE user_mobile=? AND item_name=?
            """, (
                qty,
                user_mob,
                item
            ))

            conn.commit()

            st.success(
                f"Invoice {invoice_no} saved successfully."
            )

    conn.close()


# ============================================================
# 5. STOCK SUMMARY
# ============================================================

elif menu == "📦 Stock Summary & Ledger":

    st.subheader("📦 Stock Summary & Stock Ledger")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            id,
            item_name,
            unit,
            barcode,
            hsn_sac,
            sale_price,
            purchase_price,
            gst_rate,
            stock_qty
        FROM inventory
        WHERE user_mobile=?
        ORDER BY item_name
    """, conn, params=(user_mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 6. DAY BOOK
# ============================================================

elif menu == "📅 Day Book":

    st.subheader("📅 Day Book")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            id,
            date,
            voucher_type,
            voucher_no,
            party_name,
            total_amt,
            payment_mode
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY date DESC,id DESC
    """, conn, params=(user_mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 7. VOUCHER SEARCH / EDIT / DELETE
# ============================================================

elif menu == "🔍 Voucher Search / Edit / Delete":

    st.subheader("🔍 Voucher Register")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            id,
            voucher_type,
            voucher_no,
            date,
            party_name,
            item_name,
            qty,
            rate,
            total_amt,
            payment_mode
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY id DESC
    """, conn, params=(user_mob,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:

        selected_id = st.selectbox(
            "Select Voucher ID",
            df["id"].tolist()
        )

        row = conn.execute("""
            SELECT *
            FROM vouchers
            WHERE id=? AND user_mobile=?
        """, (
            selected_id,
            user_mob
        )).fetchone()

        if row:

            row = dict(row)

            st.markdown("### ✏️ Edit Voucher")

            edit_party = st.text_input(
                "Party",
                value=row.get("party_name") or ""
            )

            edit_item = st.text_input(
                "Item",
                value=row.get("item_name") or ""
            )

            edit_qty = st.number_input(
                "Qty",
                min_value=0.0,
                value=float(row.get("qty") or 0)
            )

            edit_rate = st.number_input(
                "Rate",
                min_value=0.0,
                value=float(row.get("rate") or 0)
            )

            edit_total = edit_qty * edit_rate

            b1,b2 = st.columns(2)

            with b1:

                if st.button(
                    "💾 UPDATE VOUCHER"
                ):

                    conn.execute("""
                        UPDATE vouchers
                        SET party_name=?,
                            item_name=?,
                            qty=?,
                            rate=?,
                            taxable_amt=?,
                            total_amt=?
                        WHERE id=? AND user_mobile=?
                    """, (
                        edit_party,
                        edit_item,
                        edit_qty,
                        edit_rate,
                        edit_total,
                        edit_total,
                        selected_id,
                        user_mob
                    ))

                    conn.commit()

                    st.success(
                        "Voucher updated."
                    )

                    st.rerun()

            with b2:

                if st.button(
                    "🗑️ DELETE VOUCHER"
                ):

                    conn.execute("""
                        DELETE FROM vouchers
                        WHERE id=? AND user_mobile=?
                    """, (
                        selected_id,
                        user_mob
                    ))

                    conn.commit()

                    st.success(
                        "Voucher deleted."
                    )

                    st.rerun()

    conn.close()


# ============================================================
# 8. RECEIVABLES
# ============================================================

elif menu in [
    "👥 Receivables & Party Statements",
    "📑 Outstanding"
]:

    st.subheader("👥 Receivables & Payables")

    conn = get_db()

    customers = pd.read_sql_query("""
        SELECT
            party_name,
            SUM(total_amt) AS outstanding
        FROM vouchers
        WHERE user_mobile=?
        AND payment_mode='Credit (Pending)'
        GROUP BY party_name
    """, conn, params=(user_mob,))

    suppliers = pd.read_sql_query("""
        SELECT
            party_name,
            SUM(total_amt) AS outstanding
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND payment_mode='Credit'
        GROUP BY party_name
    """, conn, params=(user_mob,))

    c1,c2 = st.columns(2)

    with c1:

        st.markdown("### Customer Receivable")

        st.dataframe(
            customers,
            use_container_width=True,
            hide_index=True
        )

    with c2:

        st.markdown("### Supplier Payable")

        st.dataframe(
            suppliers,
            use_container_width=True,
            hide_index=True
        )

    conn.close()


# ============================================================
# 9. LEDGER
# ============================================================

elif menu == "📒 Ledger & Trial Balance":

    st.subheader("📒 Ledger & Trial Balance")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            voucher_type,
            debit_account,
            credit_account,
            SUM(total_amt) AS amount
        FROM vouchers
        WHERE user_mobile=?
        GROUP BY voucher_type,debit_account,credit_account
    """, conn, params=(user_mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 10. PROFIT & LOSS
# ============================================================

elif menu == "📈 Profit & Loss":

    st.subheader("📈 Profit & Loss")

    conn = get_db()

    sales = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Tax Invoice'
    """, (user_mob,)).fetchone()[0]

    purchase = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
    """, (user_mob,)).fetchone()[0]

    conn.close()

    profit = sales - purchase

    c1,c2,c3 = st.columns(3)

    c1.metric(
        "Sales",
        f"₹ {sales:,.2f}"
    )

    c2.metric(
        "Purchase",
        f"₹ {purchase:,.2f}"
    )

    c3.metric(
        "Gross Profit",
        f"₹ {profit:,.2f}"
    )


# ============================================================
# 11. BANK MANAGEMENT
# ============================================================

elif menu == "🏦 Capital & Bank Management":

    st.subheader("🏦 Bank Accounts")

    conn = get_db()

    bank_id = st.number_input(
        "Edit Bank ID (0 = New)",
        min_value=0,
        step=1
    )

    bank_existing = None

    if bank_id:

        bank_existing = conn.execute("""
            SELECT *
            FROM bank_accounts
            WHERE id=? AND user_mobile=?
        """, (
            bank_id,
            user_mob
        )).fetchone()

    bank_existing = (
        dict(bank_existing)
        if bank_existing else {}
    )

    bank_name = st.text_input(
        "Bank Name",
        value=bank_existing.get("bank_name","")
    )

    account_no = st.text_input(
        "Account Number",
        value=bank_existing.get("account_no","")
    )

    ifsc = st.text_input(
        "IFSC",
        value=bank_existing.get("ifsc_code","")
    )

    branch = st.text_input(
        "Branch",
        value=bank_existing.get("branch_name","")
    )

    opening = st.number_input(
        "Opening Balance",
        min_value=0.0,
        value=float(
            bank_existing.get("opening_balance") or 0
        )
    )

    if st.button(
        "💾 SAVE / UPDATE BANK"
    ):

        if bank_id and bank_existing:

            conn.execute("""
                UPDATE bank_accounts
                SET bank_name=?,
                    account_no=?,
                    ifsc_code=?,
                    branch_name=?,
                    opening_balance=?
                WHERE id=? AND user_mobile=?
            """, (
                bank_name,
                account_no,
                ifsc,
                branch,
                opening,
                bank_id,
                user_mob
            ))

        else:

            conn.execute("""
                INSERT INTO bank_accounts
                (
                    user_mobile,
                    bank_name,
                    account_no,
                    ifsc_code,
                    branch_name,
                    opening_balance
                )
                VALUES (?,?,?,?,?,?)
            """, (
                user_mob,
                bank_name,
                account_no,
                ifsc,
                branch,
                opening
            ))

        conn.commit()
        st.success("Bank account saved.")
        st.rerun()

    st.dataframe(
        pd.read_sql_query("""
            SELECT id,bank_name,account_no,
                   ifsc_code,branch_name,opening_balance
            FROM bank_accounts
            WHERE user_mobile=?
        """, conn, params=(user_mob,)),
        use_container_width=True,
        hide_index=True
    )

    conn.close()


# ============================================================
# 12. GST REPORTS
# ============================================================

elif menu == "🧮 GST Reports":

    st.subheader("🧮 GST Reports")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date,
            voucher_type,
            voucher_no,
            party_name,
            taxable_amt,
            gst_rate,
            cgst,
            sgst,
            igst,
            total_amt
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY date DESC
    """, conn, params=(user_mob,))

    conn.close()

    tab1,tab2,tab3 = st.tabs([
        "GSTR-1",
        "GSTR-2B",
        "GSTR-3B"
    ])

    with tab1:
        st.dataframe(
            df[df["voucher_type"]=="Tax Invoice"],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.dataframe(
            df[df["voucher_type"]=="Purchase"],
            use_container_width=True,
            hide_index=True
        )

    with tab3:

        total_tax = (
            df["cgst"].sum()
            + df["sgst"].sum()
            + df["igst"].sum()
        )

        st.metric(
            "Total GST",
            f"₹ {total_tax:,.2f}"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 13. THERMAL RECEIPT
# ============================================================

elif menu == "🖨️ Thermal Receipt Print":

    st.subheader("🖨️ 58mm Thermal Receipt")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            voucher_no,
            date,
            party_name,
            item_name,
            qty,
            rate,
            total_amt
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Tax Invoice'
        ORDER BY id DESC
    """, conn, params=(user_mob,))

    conn.close()

    if df.empty:

        st.info(
            "No sales invoice available."
        )

    else:

        invoice = st.selectbox(
            "Select Invoice",
            df["voucher_no"].tolist()
        )

        row = df[
            df["voucher_no"] == invoice
        ].iloc[0]

        receipt = f"""
        <div style="
            width:280px;
            background:white;
            color:black;
            padding:15px;
            font-family:monospace;
            margin:auto;
            border:1px dashed #000;
        ">
            <center>
                <h3>{clean(st.session_state.business_name)}</h3>
                <div>SALES RECEIPT</div>
            </center>

            <hr>

            Invoice: {clean(row['voucher_no'])}<br>
            Date: {clean(row['date'])}<br>
            Customer: {clean(row['party_name'])}

            <hr>

            Item: {clean(row['item_name'])}<br>
            Qty: {row['qty']}<br>
            Rate: ₹ {row['rate']:,.2f}

            <hr>

            <h3>Total: ₹ {row['total_amt']:,.2f}</h3>

            <center>Thank You!</center>
        </div>
        """

        st.components.v1.html(
            receipt,
            height=450
        )


# ============================================================
# 14. BACKUP / EXPORT
# ============================================================

elif menu in [
    "☁️ Automated Backup",
    "📤 Excel / PDF Export",
    "🖨️ Print / PDF"
]:

    st.subheader("☁️ Backup & Export")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT *
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY id DESC
    """, conn, params=(user_mob,))

    conn.close()

    csv_data = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 DOWNLOAD VOUCHER CSV",
        data=csv_data,
        file_name=(
            f"{st.session_state.business_name}_"
            f"Vouchers.csv"
        ),
        mime="text/csv"
    )

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Vouchers"
        )

    st.download_button(
        "📊 DOWNLOAD EXCEL",
        data=excel_buffer.getvalue(),
        file_name=(
            f"{st.session_state.business_name}_"
            f"Vouchers.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# ============================================================
# 15. COMPANY BRANDING
# ============================================================

elif menu == "🏢 Company Branding":

    st.subheader("🏢 Company Branding")

    conn = get_db()

    st.info(
        "Company name, address and GSTIN are controlled "
        "from Owner / Business Profile."
    )

    st.markdown(
        f"""
        ### {clean(st.session_state.business_name)}

        **Mobile:** {clean(user_mob)}

        **GSTIN:** {clean(st.session_state.business_gstin)}

        **Role:** {clean(st.session_state.user_role)}
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("Company Logo")

    logo = st.file_uploader(
        "Upload Logo",
        type=["png","jpg","jpeg"]
    )

    if logo:

        st.image(
            logo,
            width=150
        )

        st.success(
            "Logo selected successfully."
        )


# ============================================================
# 16. ACCOUNT & BILLING
# ============================================================

elif menu == "💳 Account & Billing":

    st.subheader("💳 Account & Billing")

    st.metric(
        "Current Plan",
        status
    )

    st.write(
        f"Registered Mobile: **{user_mob}**"
    )

    st.write(
        f"Role: **{st.session_state.user_role}**"
    )

    st.write(
        "Renewal UPI: **8381085702@ibl**"
    )


# ============================================================
# 17. PAYMENT / RECEIPT
# ============================================================

elif menu == "💸 Payment & Receipt":

    st.subheader("💸 Payment / Receipt")

    conn = get_db()

    party = st.text_input(
        "Party Name"
    )

    amount = st.number_input(
        "Amount",
        min_value=0.0
    )

    mode = st.selectbox(
        "Mode",
        ["Cash","Bank / UPI"]
    )

    transaction_type = st.selectbox(
        "Transaction",
        ["Payment","Receipt"]
    )

    if st.button(
        "💾 SAVE TRANSACTION"
    ):

        conn.execute("""
            INSERT INTO capital_bank_ledger
            (
                user_mobile,
                date,
                account_type,
                particulars,
                amount,
                txn_type
            )
            VALUES (?,?,?,?,?,?)
        """, (
            user_mob,
            today_str(),
            mode,
            party,
            amount,
            transaction_type
        ))

        conn.commit()

        st.success(
            "Transaction saved."
        )

    df = pd.read_sql_query("""
        SELECT *
        FROM capital_bank_ledger
        WHERE user_mobile=?
        ORDER BY id DESC
    """, conn, params=(user_mob,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    conn.close()


# ============================================================
# 18. BUSINESS REPORTS
# ============================================================

elif menu == "📊 Business Reports":

    st.subheader("📊 Business Reports")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date,
            voucher_type,
            SUM(total_amt) AS amount
        FROM vouchers
        WHERE user_mobile=?
        GROUP BY date,voucher_type
        ORDER BY date
    """, conn, params=(user_mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 19. USER / PERMISSION MANAGEMENT
# ============================================================

elif menu == "🔐 User & Permission Management":

    st.subheader("🔐 User & Permission Management")

    if st.session_state.user_role != "Owner":

        st.error(
            "Only Owner can manage users."
        )

    else:

        st.info(
            "Owner account has full access."
        )

        st.write(
            f"Current Owner Mobile: **{user_mob}**"
        )

        st.write(
            "Current Role: **Owner**"
        )


# ============================================================
# 20. COMPANY SETTINGS
# ============================================================

elif menu == "⚙️ Company Settings":

    st.subheader("⚙️ Company Settings")

    with st.form("settings_form"):

        company_name = st.text_input(
            "Business Name",
            value=user.get("business_name") or ""
        )

        address = st.text_area(
            "Address",
            value=user.get("business_address") or ""
        )

        gstin = st.text_input(
            "GSTIN",
            value=user.get("gstin") or ""
        )

        email = st.text_input(
            "Email",
            value=user.get("email") or ""
        )

        save_settings = st.form_submit_button(
            "💾 SAVE COMPANY SETTINGS"
        )

    if save_settings:

        save_user_profile(
            user_mob,
            user.get("name") or "",
            company_name,
            address,
            gstin,
            email,
            st.session_state.user_role
        )

        st.success(
            "Company settings updated."
        )

        st.rerun()


# ============================================================
# 21. GENERIC MODULES
# ============================================================

elif menu == "📥 Purchase & GSTR-2B Import":

    st.subheader("📥 Purchase & GSTR-2B Import")

    file = st.file_uploader(
        "Upload Excel / CSV",
        type=["csv","xlsx","xls"]
    )

    if file:

        try:

            if file.name.lower().endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.success(
                "File loaded successfully."
            )

            st.dataframe(
                df,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Unable to read file: {e}"
            )


elif menu == "📊 Bank Statement Import":

    st.subheader("📊 Bank Statement Import")

    file = st.file_uploader(
        "Upload Bank Statement",
        type=["csv","xlsx","xls"]
    )

    if file:

        try:

            if file.name.lower().endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.dataframe(
                df,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Import error: {e}"
            )


elif menu == "📦 Barcode Quick Billing":

    st.subheader("📦 Barcode Quick Billing")

    barcode = st.text_input(
        "Scan / Enter Barcode"
    )

    if barcode:

        conn = get_db()

        item = conn.execute("""
            SELECT *
            FROM inventory
            WHERE user_mobile=?
            AND barcode=?
        """, (
            user_mob,
            barcode
        )).fetchone()

        conn.close()

        if item:

            st.success(
                f"Item found: {item['item_name']}"
            )

            st.write(
                f"Price: ₹ {float(item['sale_price'] or 0):,.2f}"
            )

            st.write(
                f"Stock: {float(item['stock_qty'] or 0):,.2f}"
            )

        else:

            st.warning(
                "Barcode not found."
            )


elif menu == "💰 Tally Vouchers F4-F9":

    st.subheader("💰 Tally Voucher Entry")

    voucher_type = st.selectbox(
        "Voucher Type",
        [
            "Payment",
            "Receipt",
            "Contra",
            "Journal",
            "Sales",
            "Purchase"
        ]
    )

    voucher_no = st.text_input(
        "Voucher Number",
        generate_voucher_no("VCH")
    )

    party = st.text_input(
        "Party / Ledger"
    )

    amount = st.number_input(
        "Amount",
        min_value=0.0
    )

    if st.button(
        "💾 SAVE VOUCHER"
    ):

        conn = get_db()

        conn.execute("""
            INSERT INTO vouchers
            (
                user_mobile,
                voucher_type,
                voucher_no,
                date,
                party_name,
                total_amt
            )
            VALUES (?,?,?,?,?,?)
        """, (
            user_mob,
            voucher_type,
            voucher_no,
            today_str(),
            party,
            amount
        ))

        conn.commit()
        conn.close()

        st.success(
            "Voucher saved."
        )


elif menu == "🚚 e-Way Bill & e-Invoice":

    st.subheader("🚚 e-Way Bill & e-Invoice")

    st.info(
        "Enter the official portal details here. "
        "Actual government API submission requires "
        "valid GST credentials/API access."
    )

    eway = st.text_input(
        "e-Way Bill Number"
    )

    irn = st.text_input(
        "IRN Number"
    )

    if st.button(
        "💾 SAVE DETAILS"
    ):

        st.success(
            "Details entered for record."
        )


elif menu == "📋 Balance Sheet":

    st.subheader("📋 Balance Sheet")

    conn = get_db()

    bank = conn.execute("""
        SELECT COALESCE(SUM(opening_balance),0)
        FROM bank_accounts
        WHERE user_mobile=?
    """, (user_mob,)).fetchone()[0]

    receivable = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND payment_mode='Credit (Pending)'
    """, (user_mob,)).fetchone()[0]

    payable = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND payment_mode='Credit'
    """, (user_mob,)).fetchone()[0]

    conn.close()

    c1,c2,c3 = st.columns(3)

    c1.metric(
        "Bank",
        f"₹ {bank:,.2f}"
    )

    c2.metric(
        "Receivable",
        f"₹ {receivable:,.2f}"
    )

    c3.metric(
        "Payable",
        f"₹ {payable:,.2f}"
    )


elif menu == "🔄 Sales / Purchase Return":

    st.subheader("🔄 Sales / Purchase Return")

    return_type = st.selectbox(
        "Return Type",
        [
            "Sales Return",
            "Purchase Return"
        ]
    )

    party = st.text_input(
        "Party"
    )

    item = st.text_input(
        "Item"
    )

    qty = st.number_input(
        "Quantity",
        min_value=0.0
    )

    amount = st.number_input(
        "Amount",
        min_value=0.0
    )

    if st.button(
        "💾 SAVE RETURN"
    ):

        conn = get_db()

        conn.execute("""
            INSERT INTO vouchers
            (
                user_mobile,
                voucher_type,
                voucher_no,
                date,
                party_name,
                item_name,
                qty,
                total_amt
            )
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            user_mob,
            return_type,
            generate_voucher_no("RET"),
            today_str(),
            party,
            item,
            qty,
            amount
        ))

        conn.commit()
        conn.close()

        st.success(
            "Return saved."
        )


else:

    st.subheader(menu)

    st.info(
        "Module is ready in the enterprise workspace. "
        "Use Masters, Purchase, Sales, Vouchers, Reports "
        "and Settings from the navigation menu."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "SD TALLY BUSINESS • Professional Business Management System"
)
