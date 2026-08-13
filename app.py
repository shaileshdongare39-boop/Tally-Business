# ================================================================
# SD TALLY BUSINESS - PROFESSIONAL ALL-IN-ONE ERP
# Single File Streamlit ERP / Billing / Accounting Application
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

# Optional libraries
try:
    import plotly.express as px
except Exception:
    px = None

try:
    import extra_streamlit_components as stx
    COOKIES_OK = True
except Exception:
    COOKIES_OK = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False


# ================================================================
# PAGE CONFIG
# ================================================================

st.set_page_config(
    page_title="SD Tally Business",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ================================================================
# CONSTANTS & DATABASE PATH FIX FOR STREAMLIT CLOUD
# ================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sd_tally_v3.db")

ROLES = ["Owner", "Staff"]

UNITS = [
    "PCS", "KG", "GM", "LTR", "ML", "MTR", "CM",
    "BOX", "BAG", "PACK", "DOZEN", "SQFT", "SET"
]

GST_RATES = [0, 5, 12, 18, 28]

PAYMENT_MODES = [
    "Cash",
    "Bank",
    "UPI",
    "Credit"
]

VOUCHER_TYPES = [
    "Sales",
    "Purchase",
    "Sales Return",
    "Purchase Return",
    "Payment",
    "Receipt",
    "Contra",
    "Journal"
]


# ================================================================
# GLOBAL CSS - HIGH STANDARD ENTERPRISE LOOK
# ================================================================

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b1329 !important;
    color: #f1f5f9 !important;
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
}

[data-testid="stSidebar"] {
    background: #111c44 !important;
    border-right: 1px solid #1e293b !important;
}

.main-title {
    background: linear-gradient(135deg, #111c44 0%, #0b1329 100%);
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #1e293b;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    margin-bottom: 25px;
    text-align: center;
}

.main-title h1 {
    color: #38bdf8 !important;
    margin: 0;
    font-size: 2.2rem;
    font-weight: 800;
}

.card {
    background: #111c44;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #1e293b;
    margin-bottom: 15px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.stButton > button {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    width: 100%;
    min-height: 46px;
    font-weight: 700;
    border-radius: 8px;
    border: none !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
}

div[data-baseweb="input"] > div {
    background-color: #0b1329 !important;
    border-color: #1e293b !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

[data-testid="stMetric"] {
    background: #111c44 !important;
    border-radius: 12px;
    border: 1px solid #1e293b;
    padding: 18px;
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
        name TEXT,
        mobile TEXT,
        role TEXT DEFAULT 'Owner',
        business_name TEXT,
        business_address TEXT,
        gstin TEXT,
        created_at TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        sku TEXT,
        barcode TEXT,
        hsn TEXT,
        unit TEXT DEFAULT 'PCS',
        gst_rate REAL DEFAULT 0,
        sale_price REAL DEFAULT 0,
        purchase_price REAL DEFAULT 0,
        opening_stock REAL DEFAULT 0,
        min_stock REAL DEFAULT 0,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS godowns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        address TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        party_type TEXT NOT NULL,
        mobile TEXT,
        email TEXT,
        gstin TEXT,
        address TEXT,
        opening_balance REAL DEFAULT 0,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        bank_name TEXT NOT NULL,
        account_no TEXT,
        ifsc TEXT,
        branch TEXT,
        opening_balance REAL DEFAULT 0,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        voucher_type TEXT NOT NULL,
        voucher_no TEXT NOT NULL,
        voucher_date TEXT NOT NULL,
        party_id INTEGER,
        party_name TEXT,
        payment_mode TEXT,
        reference TEXT,
        subtotal REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        taxable REAL DEFAULT 0,
        cgst REAL DEFAULT 0,
        sgst REAL DEFAULT 0,
        igst REAL DEFAULT 0,
        total REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS voucher_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voucher_id INTEGER NOT NULL,
        item_id INTEGER,
        item_name TEXT,
        qty REAL DEFAULT 0,
        rate REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        taxable REAL DEFAULT 0,
        gst_rate REAL DEFAULT 0,
        cgst REAL DEFAULT 0,
        sgst REAL DEFAULT 0,
        igst REAL DEFAULT 0,
        total REAL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        voucher_id INTEGER,
        txn_date TEXT NOT NULL,
        txn_type TEXT NOT NULL,
        qty REAL DEFAULT 0,
        rate REAL DEFAULT 0,
        remarks TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledger_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        entry_date TEXT NOT NULL,
        voucher_id INTEGER,
        account_name TEXT,
        debit REAL DEFAULT 0,
        credit REAL DEFAULT 0,
        narration TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        company_name TEXT,
        address TEXT,
        gstin TEXT,
        phone TEXT,
        email TEXT,
        invoice_prefix TEXT DEFAULT 'INV',
        next_invoice INTEGER DEFAULT 1,
        upi_id TEXT,
        payment_note TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        details TEXT,
        action_time TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================================================================
# SESSION MANAGEMENT (NO AUTO LOGOUT)
# ================================================================

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "cart" not in st.session_state:
    st.session_state.cart = []

if "editing_item" not in st.session_state:
    st.session_state.editing_item = None


# ================================================================
# COOKIE MANAGER
# ================================================================

def get_cookie_manager():
    if COOKIES_OK:
        if "cookie_manager" not in st.session_state:
            st.session_state.cookie_manager = stx.CookieManager(key="sd_tally_cookie_mgr")
        return st.session_state.cookie_manager
    return None

def check_auto_login():
    if "persistent_user_id" in st.session_state and st.session_state.user_id is None:
        u_id = st.session_state.persistent_user_id
        conn = db()
        user = conn.execute("SELECT id, username, role FROM users WHERE id=? AND active=1", (u_id,)).fetchone()
        conn.close()
        if user:
            st.session_state.user_id = user["id"]
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]
            ensure_settings()
    else:
        cm = get_cookie_manager()
        if cm:
            try:
                saved_user_id = cm.get(cookie="sd_tally_user_id")
                if saved_user_id and st.session_state.user_id is None:
                    init_db()
                    conn = db()
                    user = conn.execute("SELECT id, username, role FROM users WHERE id=? AND active=1", (int(saved_user_id),)).fetchone()
                    conn.close()
                    if user:
                        st.session_state.user_id = user["id"]
                        st.session_state.username = user["username"]
                        st.session_state.role = user["role"]
                        st.session_state.persistent_user_id = user["id"]
                        ensure_settings()
            except Exception:
                pass


# ================================================================
# HELPERS
# ================================================================

def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_text():
    return date.today().isoformat()


def money(value):
    try:
        return f"₹ {float(value):,.2f}"
    except Exception:
        return "₹ 0.00"


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password, password_hash):
    return secrets.compare_digest(
        hash_password(password),
        password_hash
    )


def user_is_owner():
    return st.session_state.role == "Owner"


def audit(action, details=""):
    conn = db()
    conn.execute(
        """
        INSERT INTO audit_log
        (user_id, action, details, action_time)
        VALUES (?, ?, ?, ?)
        """,
        (
            st.session_state.user_id,
            action,
            details,
            now_text()
        )
    )
    conn.commit()
    conn.close()


def get_user():
    conn = db()
    row = conn.execute(
        """
        SELECT id, username, name, mobile, role,
               business_name, business_address, gstin
        FROM users
        WHERE id=?
        """,
        (st.session_state.user_id,)
    ).fetchone()
    conn.close()
    return row


def get_settings():
    conn = db()
    row = conn.execute(
        "SELECT * FROM settings WHERE user_id=?",
        (st.session_state.user_id,)
    ).fetchone()
    conn.close()
    return row


def ensure_settings():
    conn = db()
    exists = conn.execute(
        "SELECT user_id FROM settings WHERE user_id=?",
        (st.session_state.user_id,)
    ).fetchone()

    if not exists:
        u = get_user()
        conn.execute("""
            INSERT INTO settings
            (user_id, company_name, address, gstin, phone, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.user_id,
            u["business_name"] or "",
            u["business_address"] or "",
            u["gstin"] or "",
            u["mobile"] or "",
            ""
        ))
        conn.commit()

    conn.close()


def next_invoice_no():
    conn = db()

    row = conn.execute(
        """
        SELECT invoice_prefix, next_invoice
        FROM settings
        WHERE user_id=?
        """,
        (st.session_state.user_id,)
    ).fetchone()

    if not row:
        prefix = "INV"
        number = 1
        conn.execute("""
            INSERT INTO settings
            (user_id, invoice_prefix, next_invoice)
            VALUES (?, ?, ?)
        """, (
            st.session_state.user_id,
            prefix,
            number + 1
        ))
    else:
        prefix = row["invoice_prefix"] or "INV"
        number = row["next_invoice"] or 1

        conn.execute("""
            UPDATE settings
            SET next_invoice=?
            WHERE user_id=?
        """, (
            number + 1,
            st.session_state.user_id
        ))

    conn.commit()
    conn.close()

    return f"{prefix}-{number:05d}"


def get_items():
    conn = db()
    df = pd.read_sql_query(
        """
        SELECT *
        FROM items
        WHERE user_id=? AND active=1
        ORDER BY name
        """,
        conn,
        params=(st.session_state.user_id,)
    )
    conn.close()
    return df


def get_parties(party_type=None):
    conn = db()

    if party_type:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM parties
            WHERE user_id=? AND party_type=? AND active=1
            ORDER BY name
            """,
            conn,
            params=(st.session_state.user_id, party_type)
        )
    else:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM parties
            WHERE user_id=? AND active=1
            ORDER BY name
            """,
            conn,
            params=(st.session_state.user_id,)
        )

    conn.close()
    return df


def current_stock(item_id):
    conn = db()

    opening = conn.execute(
        """
        SELECT opening_stock
        FROM items
        WHERE id=? AND user_id=?
        """,
        (item_id, st.session_state.user_id)
    ).fetchone()

    total = conn.execute(
        """
        SELECT COALESCE(SUM(qty),0)
        FROM stock_transactions
        WHERE item_id=? AND user_id=?
        """,
        (item_id, st.session_state.user_id)
    ).fetchone()[0]

    conn.close()

    return float(opening["opening_stock"] if opening else 0) + float(total or 0)


def add_stock_transaction(
    item_id,
    voucher_id,
    txn_type,
    qty,
    rate,
    remarks=""
):
    conn = db()

    conn.execute("""
        INSERT INTO stock_transactions
        (
            user_id,
            item_id,
            voucher_id,
            txn_date,
            txn_type,
            qty,
            rate,
            remarks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state.user_id,
        item_id,
        voucher_id,
        today_text(),
        txn_type,
        qty,
        rate,
        remarks
    ))

    conn.commit()
    conn.close()


def add_ledger(
    account_name,
    debit,
    credit,
    voucher_id=None,
    narration=""
):
    conn = db()

    conn.execute("""
        INSERT INTO ledger_entries
        (
            user_id,
            entry_date,
            voucher_id,
            account_name,
            debit,
            credit,
            narration
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state.user_id,
        today_text(),
        voucher_id,
        account_name,
        debit,
        credit,
        narration
    ))

    conn.commit()
    conn.close()


def calculate_line(qty, rate, discount, gst_rate):
    gross = qty * rate
    discount_amount = gross * discount / 100
    taxable = gross - discount_amount

    gst = taxable * gst_rate / 100

    cgst = gst / 2
    sgst = gst / 2
    igst = 0

    total = taxable + cgst + sgst + igst

    return {
        "qty": qty,
        "rate": rate,
        "discount": discount_amount,
        "taxable": taxable,
        "gst_rate": gst_rate,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "total": total
    }


# ================================================================
# AUTHENTICATION & PASSWORD RECOVERY
# ================================================================

def register_user(
    username,
    password,
    name,
    mobile,
    business_name
):
    username = clean(username).lower()

    if len(username) < 4:
        return False, "Username must contain at least 4 characters."

    if len(password) < 6:
        return False, "Password must contain at least 6 characters."

    if not business_name.strip():
        return False, "Business name is required."

    init_db()

    conn = db()

    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users
            (
                username,
                password_hash,
                name,
                mobile,
                role,
                business_name,
                created_at
            )
            VALUES (?, ?, ?, ?, 'Owner', ?, ?)
        """, (
            username,
            hash_password(password),
            name,
            mobile,
            business_name,
            now_text()
        ))

        user_id = cur.lastrowid

        cur.execute("""
            INSERT INTO settings
            (
                user_id,
                company_name,
                phone
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            business_name,
            mobile
        ))

        conn.commit()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "Username already exists."

    finally:
        conn.close()


def login_user(username, password):
    init_db()

    conn = db()

    row = conn.execute("""
        SELECT id, username, password_hash, role
        FROM users
        WHERE username=? AND active=1
    """, (
        clean(username).lower(),
    )).fetchone()

    conn.close()

    if not row:
        return False

    if not verify_password(password, row["password_hash"]):
        return False

    st.session_state.user_id = row["id"]
    st.session_state.username = row["username"]
    st.session_state.role = row["role"]
    st.session_state.persistent_user_id = row["id"]

    ensure_settings()

    cm = get_cookie_manager()
    if cm:
        try:
            cm.set("sd_tally_user_id", str(row["id"]), expires_at=datetime.now() + timedelta(days=30))
        except Exception:
            pass

    return True


def reset_password_with_mobile(mobile, new_password):
    init_db()
    conn = db()
    row = conn.execute("SELECT id FROM users WHERE mobile=? AND active=1", (clean(mobile),)).fetchone()
    if row:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_password), row["id"]))
        conn.commit()
        conn.close()
        return True, "Password updated successfully!"
    conn.close()
    return False, "Mobile number is not registered."


def get_username_by_mobile(mobile):
    init_db()
    conn = db()
    row = conn.execute("SELECT username FROM users WHERE mobile=? AND active=1", (clean(mobile),)).fetchone()
    conn.close()
    if row:
        return True, f"Your Username: **{row['username']}**"
    return False, "Mobile number is not registered."


# ================================================================
# CLEAN LOGIN PAGE (ONLY "SD Tally Business")
# ================================================================

def login_page():

    st.markdown("""
    <div class="main-title">
        <h1>🏢 SD Tally Business</h1>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🔐 Sign In",
        "📝 Register Account",
        "🔑 Recover Credentials"
    ])

    with tab1:

        st.subheader("Sign In")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "LOGIN",
            type="primary",
            use_container_width=True
        ):
            if login_user(username, password):
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:

        st.subheader("Create Account")

        r_username = st.text_input(
            "Username"
        )

        r_password = st.text_input(
            "Password",
            type="password"
        )

        r_confirm = st.text_input(
            "Confirm Password",
            type="password"
        )

        r_name = st.text_input(
            "Owner Name"
        )

        r_mobile = st.text_input(
            "Mobile Number"
        )

        r_business = st.text_input(
            "Business Name"
        )

        if st.button(
            "REGISTER",
            type="primary"
        ):

            if r_password != r_confirm:
                st.error("Passwords do not match.")

            else:
                ok, message = register_user(
                    r_username,
                    r_password,
                    r_name,
                    r_mobile,
                    r_business
                )

                if ok:
                    st.success(message)
                else:
                    st.error(message)

    with tab3:
        st.subheader("🔑 Credential Recovery")
        option = st.radio("Select Option", ["Find Username", "Reset Password"])

        if option == "Find Username":
            f_mobile = st.text_input("Enter Mobile Number", key="find_user_mobile")
            if st.button("Get Username", type="primary"):
                if f_mobile:
                    ok, msg = get_username_by_mobile(f_mobile)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        elif option == "Reset Password":
            r_mobile = st.text_input("Enter Mobile Number", key="reset_pass_mobile")
            new_pass = st.text_input("New Password", type="password", key="reset_new_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reset_confirm_pass")

            if st.button("Update Password", type="primary"):
                if new_pass == confirm_pass:
                    ok, msg = reset_password_with_mobile(r_mobile, new_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


# ================================================================
# SIDEBAR
# ================================================================

def sidebar():

    user = get_user()

    st.sidebar.markdown(
        f"""
        <div class="card">
        <b>👤 User:</b> {html.escape(user['name'] or user['username'])}<br><br>
        <b>🏢 Business:</b> {html.escape(user['business_name'] or "-")}<br><br>
        <b>🔑 Role:</b> {html.escape(user['role'])}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.sidebar.button(
        "🚪 LOGOUT",
        use_container_width=True
    ):
        cm = get_cookie_manager()
        if cm:
            try:
                cm.delete("sd_tally_user_id")
            except Exception:
                pass
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.persistent_user_id = None
        st.session_state.cart = []
        st.rerun()


# ================================================================
# DASHBOARD
# ================================================================

def dashboard():

    st.subheader("📊 Business Overview")

    uid = st.session_state.user_id
    conn = db()

    sales = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Sales'
    """, (uid,)).fetchone()[0]

    purchases = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Purchase'
    """, (uid,)).fetchone()[0]

    sales_returns = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Sales Return'
    """, (uid,)).fetchone()[0]

    purchase_returns = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Purchase Return'
    """, (uid,)).fetchone()[0]

    item_count = conn.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE user_id=? AND active=1
    """, (uid,)).fetchone()[0]

    party_count = conn.execute("""
        SELECT COUNT(*)
        FROM parties
        WHERE user_id=? AND active=1
    """, (uid,)).fetchone()[0]

    conn.close()

    net_sales = float(sales) - float(sales_returns)
    net_purchase = float(purchases) - float(purchase_returns)
    gross = net_sales - net_purchase

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Net Sales",
        money(net_sales)
    )

    c2.metric(
        "Net Purchases",
        money(net_purchase)
    )

    c3.metric(
        "Gross Profit",
        money(gross)
    )

    c4.metric(
        "Items / Parties",
        f"{item_count} / {party_count}"
    )

    st.markdown("---")

    if px:

        chart_df = pd.DataFrame({
            "Category": [
                "Sales",
                "Purchases",
                "Sales Return",
                "Purchase Return"
            ],
            "Amount": [
                sales,
                purchases,
                sales_returns,
                purchase_returns
            ]
        })

        fig = px.bar(
            chart_df,
            x="Category",
            y="Amount",
            title="Financial Stream Overview",
            color="Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ================================================================
# ITEM MASTER
# ================================================================

def item_master():

    st.subheader("📦 Product & Inventory Master")

    tabs = st.tabs([
        "Add Product Master",
        "Inventory Directory",
        "Update Product Master"
    ])

    with tabs[0]:

        with st.form("add_item"):

            name = st.text_input(
                "Product Name *"
            )

            sku = st.text_input(
                "SKU Code"
            )

            barcode = st.text_input(
                "Barcode Value"
            )

            hsn = st.text_input(
                "HSN / SAC Code"
            )

            unit = st.selectbox(
                "Unit",
                UNITS
            )

            gst = st.selectbox(
                "GST Rate (%)",
                GST_RATES
            )

            sale_price = st.number_input(
                "Selling Rate",
                min_value=0.0,
                step=0.01
            )

            purchase_price = st.number_input(
                "Purchase Price",
                min_value=0.0,
                step=0.01
            )

            opening_stock = st.number_input(
                "Opening Stock Quantity",
                min_value=0.0,
                step=0.01
            )

            min_stock = st.number_input(
                "Low Stock Alert Quantity",
                min_value=0.0,
                step=0.01
            )

            if st.form_submit_button(
                "Save Product Master",
                type="primary"
            ):

                if name.strip():

                    conn = db()

                    conn.execute("""
                        INSERT INTO items
                        (
                            user_id,
                            name,
                            sku,
                            barcode,
                            hsn,
                            unit,
                            gst_rate,
                            sale_price,
                            purchase_price,
                            opening_stock,
                            min_stock
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        name,
                        sku,
                        barcode,
                        hsn,
                        unit,
                        gst,
                        sale_price,
                        purchase_price,
                        opening_stock,
                        min_stock
                    ))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Product Master saved successfully."
                    )

    with tabs[1]:

        df = get_items()

        if not df.empty:

            df["Current Stock"] = df["id"].apply(
                current_stock
            )

            st.dataframe(
                df[
                    [
                        "id",
                        "name",
                        "sku",
                        "unit",
                        "gst_rate",
                        "sale_price",
                        "purchase_price",
                        "Current Stock"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

    with tabs[2]:

        df = get_items()

        if not df.empty:

            selected = st.selectbox(
                "Select Product To Edit",
                df["id"].tolist(),
                format_func=lambda x:
                    df.loc[
                        df["id"] == x,
                        "name"
                    ].iloc[0]
            )

            row = df[df["id"] == selected].iloc[0]

            with st.form("edit_item"):

                name = st.text_input(
                    "Product Name",
                    value=row["name"]
                )

                sku = st.text_input(
                    "SKU Code",
                    value=row["sku"] or ""
                )

                unit = st.selectbox(
                    "Unit",
                    UNITS,
                    index=(
                        UNITS.index(row["unit"])
                        if row["unit"] in UNITS
                        else 0
                    )
                )

                gst = st.selectbox(
                    "GST Rate (%)",
                    GST_RATES,
                    index=(
                        GST_RATES.index(
                            float(row["gst_rate"])
                        )
                        if float(row["gst_rate"]) in GST_RATES
                        else 0
                    )
                )

                sale = st.number_input(
                    "Selling Price",
                    value=float(row["sale_price"])
                )

                purchase = st.number_input(
                    "Purchase Rate",
                    value=float(row["purchase_price"])
                )

                if st.form_submit_button(
                    "Update Product Master",
                    type="primary"
                ):

                    conn = db()

                    conn.execute("""
                        UPDATE items
                        SET name=?,
                            sku=?,
                            unit=?,
                            gst_rate=?,
                            sale_price=?,
                            purchase_price=?
                        WHERE id=? AND user_id=?
                    """, (
                        name,
                        sku,
                        unit,
                        gst,
                        sale,
                        purchase,
                        selected,
                        st.session_state.user_id
                    ))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Product Master updated successfully."
                    )

                    st.rerun()


# ================================================================
# PARTY MASTER
# ================================================================

def party_master():

    st.subheader("👥 Customer & Supplier Master")

    tabs = st.tabs([
        "Register Party Master",
        "Ledger Directory"
    ])

    with tabs[0]:

        with st.form("party_form"):

            name = st.text_input(
                "Party Legal Name *"
            )

            party_type = st.selectbox(
                "Contact Type",
                ["Customer", "Supplier"]
            )

            mobile = st.text_input(
                "Phone Number"
            )

            address = st.text_area(
                "Billing Address"
            )

            opening = st.number_input(
                "Opening Balance Amount",
                min_value=0.0,
                step=0.01
            )

            if st.form_submit_button(
                "Save Party Master",
                type="primary"
            ):

                if name.strip():

                    conn = db()

                    conn.execute("""
                        INSERT INTO parties
                        (
                            user_id,
                            name,
                            party_type,
                            mobile,
                            address,
                            opening_balance
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        name,
                        party_type,
                        mobile,
                        address,
                        opening
                    ))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Party Master created successfully."
                    )

    with tabs[1]:

        df = get_parties()

        if not df.empty:

            st.dataframe(
                df[
                    [
                        "id",
                        "name",
                        "party_type",
                        "mobile",
                        "address",
                        "opening_balance"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


# ================================================================
# GODOWN / WAREHOUSE
# ================================================================

def godown_master():

    st.subheader("🏭 Warehouse / Godown Management")

    with st.form("godown_form"):

        name = st.text_input(
            "Godown Name"
        )

        address = st.text_area(
            "Warehouse Location Address"
        )

        if st.form_submit_button(
            "Save Warehouse Master",
            type="primary"
        ):

            if name.strip():

                conn = db()

                conn.execute("""
                    INSERT INTO godowns
                    (user_id, name, address)
                    VALUES (?, ?, ?)
                """, (
                    st.session_state.user_id,
                    name,
                    address
                ))

                conn.commit()
                conn.close()

                st.success(
                    "Warehouse location saved."
                )

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT id, name, address
        FROM godowns
        WHERE user_id=? AND active=1
        ORDER BY name
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# TRANSACTION ENTRY
# ================================================================

def transaction_entry(voucher_type):

    st.subheader(
        f"🧾 {voucher_type} Voucher Creation Engine"
    )

    party_type = (
        "Customer"
        if voucher_type in ["Sales", "Sales Return"]
        else "Supplier"
    )

    parties, items = get_parties(party_type), get_items()

    if items.empty or parties.empty:
        st.warning(
            f"Please configure Product and {party_type} Masters first."
        )
        return

    col1, col2, col3 = st.columns(3)

    voucher_no = col1.text_input(
        "Voucher Number",
        value=next_invoice_no()
        if voucher_type == "Sales"
        else ""
    )

    voucher_date = col2.date_input(
        "Transaction Date",
        value=date.today()
    )

    payment_mode = col3.selectbox(
        "Payment Settlement Mode",
        PAYMENT_MODES
    )

    party_id = st.selectbox(
        f"Select Account Contact ({party_type})",
        parties["id"].tolist(),
        format_func=lambda x:
            parties.loc[
                parties["id"] == x,
                "name"
            ].iloc[0]
    )

    party_name = parties.loc[
        parties["id"] == party_id,
        "name"
    ].iloc[0]

    st.markdown("### Item Line Builder")

    item_id = st.selectbox(
        "Select Product Item",
        items["id"].tolist(),
        format_func=lambda x:
            items.loc[
                items["id"] == x,
                "name"
            ].iloc[0]
    )

    item_row = items[
        items["id"] == item_id
    ].iloc[0]

    c1, c2, c3 = st.columns(3)

    qty = c1.number_input(
        "Quantity",
        min_value=0.01,
        value=1.0,
        step=1.0
    )

    rate = c2.number_input(
        "Unit Rate Price",
        min_value=0.0,
        value=float(
            item_row["sale_price"]
            if voucher_type == "Sales"
            else item_row["purchase_price"]
        )
    )

    gst_rate = c3.selectbox(
        "GST Tax Rate (%)",
        GST_RATES,
        index=(
            GST_RATES.index(
                float(item_row["gst_rate"])
            )
            if float(item_row["gst_rate"]) in GST_RATES
            else 0
        )
    )

    line = calculate_line(
        qty,
        rate,
        0,
        gst_rate
    )

    if st.button(
        "➕ Add Product To Billing Cart"
    ):

        st.session_state.cart.append({
            "item_id": int(item_id),
            "item_name": item_row["name"],
            "qty": qty,
            "rate": rate,
            "discount": 0,
            "taxable": line["taxable"],
            "gst_rate": gst_rate,
            "cgst": line["cgst"],
            "sgst": line["sgst"],
            "igst": 0,
            "total": line["total"]
        })

        st.success(
            "Item appended to cart."
        )

    if st.session_state.cart:

        st.dataframe(
            pd.DataFrame(
                st.session_state.cart
            )[
                [
                    "item_name",
                    "qty",
                    "rate",
                    "taxable",
                    "gst_rate",
                    "total"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        total = sum(
            x["total"]
            for x in st.session_state.cart
        )

        st.markdown(
            f"### Grand Invoice Total: **{money(total)}**"
        )

        if st.button(
            "💾 EXECUTE VOUCHER & POST TO LEDGER",
            type="primary"
        ):

            save_voucher(
                voucher_type,
                voucher_no,
                voucher_date,
                party_id,
                party_name,
                payment_mode,
                ""
            )


def save_voucher(
    voucher_type,
    voucher_no,
    voucher_date,
    party_id,
    party_name,
    payment_mode,
    notes
):

    conn = db()

    cur = conn.cursor()

    total = sum(
        x["total"]
        for x in st.session_state.cart
    )

    cur.execute("""
        INSERT INTO vouchers
        (
            user_id,
            voucher_type,
            voucher_no,
            voucher_date,
            party_id,
            party_name,
            payment_mode,
            total,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state.user_id,
        voucher_type,
        voucher_no,
        str(voucher_date),
        party_id,
        party_name,
        payment_mode,
        total,
        now_text()
    ))

    v_id = cur.lastrowid

    for line in st.session_state.cart:

        cur.execute("""
            INSERT INTO voucher_items
            (
                voucher_id,
                item_id,
                item_name,
                qty,
                rate,
                taxable,
                gst_rate,
                total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v_id,
            line["item_id"],
            line["item_name"],
            line["qty"],
            line["rate"],
            line["taxable"],
            line["gst_rate"],
            line["total"]
        ))

        stock_qty = (
            -abs(line["qty"])
            if voucher_type == "Sales"
            else abs(line["qty"])
        )

        cur.execute("""
            INSERT INTO stock_transactions
            (
                user_id,
                item_id,
                voucher_id,
                txn_date,
                txn_type,
                qty,
                rate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.user_id,
            line["item_id"],
            v_id,
            str(voucher_date),
            voucher_type,
            stock_qty,
            line["rate"]
        ))

    conn.commit()
    conn.close()

    st.session_state.cart = []

    st.success(
        "Voucher committed successfully."
    )

    st.rerun()


# ================================================================
# RETURNS
# ================================================================

def returns_module():

    st.subheader(
        "🔄 Credit Notes & Debit Notes (Returns)"
    )

    typ = st.selectbox(
        "Return Voucher Type",
        [
            "Sales Return",
            "Purchase Return"
        ]
    )

    transaction_entry(
        typ
    )


# ================================================================
# STOCK SUMMARY
# ================================================================

def stock_module():

    st.subheader(
        "📦 Stock Valuation Summary & Inventory Ledger"
    )

    df = get_items()

    if df.empty:
        st.info("No product items available.")
        return

    df["Current Stock"] = df["id"].apply(
        current_stock
    )

    st.dataframe(
        df[
            [
                "id",
                "name",
                "sku",
                "unit",
                "sale_price",
                "purchase_price",
                "Current Stock"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# BARCODE BILLING
# ================================================================

def barcode_billing():

    st.subheader("📦 Barcode Quick Billing Engine")

    barcode = st.text_input(
        "Scan / Enter Barcode Value"
    )

    if barcode:

        conn = db()

        row = conn.execute("""
            SELECT id, name, sale_price, gst_rate
            FROM items
            WHERE user_id=? AND barcode=? AND active=1
        """, (
            st.session_state.user_id,
            barcode
        )).fetchone()

        conn.close()

        if row:

            st.success(
                f"Product Identified: {row['name']}"
            )

            qty = st.number_input(
                "Quantity",
                min_value=1.0,
                value=1.0
            )

            line = calculate_line(
                qty,
                float(row['sale_price']),
                0,
                float(row['gst_rate'])
            )

            if st.button(
                "Add Product To Cart"
            ):

                st.session_state.cart.append({
                    "item_id": row['id'],
                    "item_name": row['name'],
                    "qty": qty,
                    "rate": row['sale_price'],
                    "taxable": line["taxable"],
                    "gst_rate": row['gst_rate'],
                    "total": line["total"]
                })

                st.success("Added to cart.")


# ================================================================
# PAYMENT & RECEIPT
# ================================================================

def payment_receipt():

    st.subheader("💰 Payment & Receipt Transactions")

    typ = st.selectbox(
        "Transaction Type",
        ["Payment", "Receipt"]
    )

    parties = get_parties()

    if not parties.empty:

        party_id = st.selectbox(
            "Account Party",
            parties["id"].tolist(),
            format_func=lambda x:
                parties.loc[
                    parties["id"] == x,
                    "name"
                ].iloc[0]
        )

        amount = st.number_input(
            "Amount",
            min_value=0.01
        )

        mode = st.selectbox(
            "Settlement Mode",
            PAYMENT_MODES
        )

        if st.button(
            f"Save {typ} Voucher",
            type="primary"
        ):

            add_ledger(
                parties.loc[
                    parties["id"] == party_id,
                    "name"
                ].iloc[0],
                amount if typ == "Receipt" else 0,
                amount if typ == "Payment" else 0
            )

            st.success(
                f"{typ} Voucher Saved."
            )


# ================================================================
# BANK ACCOUNTS
# ================================================================

def bank_accounts():

    st.subheader("🏦 Bank Account Management")

    with st.form("bank_form"):

        bank_name = st.text_input(
            "Bank Name"
        )

        account = st.text_input(
            "Account Number"
        )

        ifsc = st.text_input(
            "IFSC Code"
        )

        opening = st.number_input(
            "Opening Balance",
            min_value=0.0
        )

        if st.form_submit_button(
            "Save Bank Account",
            type="primary"
        ):

            conn = db()

            conn.execute("""
                INSERT INTO bank_accounts
                (user_id, bank_name, account_no, ifsc, opening_balance)
                VALUES (?, ?, ?, ?, ?)
            """, (
                st.session_state.user_id,
                bank_name,
                account,
                ifsc,
                opening
            ))

            conn.commit()
            conn.close()

            st.success(
                "Bank Account Configured."
            )


# ================================================================
# GST REPORTS
# ================================================================

def gst_reports():

    st.subheader(
        "🧮 GST Compliance & Tax Reports"
    )

    conn = db()

    sales = pd.read_sql_query(
        """
        SELECT voucher_no, voucher_date, party_name, total
        FROM vouchers
        WHERE user_id=? AND voucher_type='Sales'
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    conn.close()

    st.dataframe(
        sales,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# NAVIGATION BOARD
# ================================================================

def app():

    sidebar()

    user = get_user()

    st.markdown(
        f"""
        <div class="main-title">
            <h1>🏢 SD Tally Business</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    menu = [
        "📊 Dashboard",
        "📦 Item Master",
        "👥 Customer & Supplier Master",
        "🏭 Godown Management",
        "🧾 Sales Invoice",
        "🛒 Purchase Entry",
        "🔄 Sales / Purchase Return",
        "📦 Stock Summary & Ledger",
        "📦 Barcode Quick Billing",
        "💰 Payment & Receipt",
        "🏦 Bank Accounts",
        "🧮 GST Reports",
        "🏢 Company Profile"
    ]

    selected = st.sidebar.selectbox(
        "📌 Navigation Board",
        menu
    )

    if selected == "📊 Dashboard":
        dashboard()

    elif selected == "📦 Item Master":
        item_master()

    elif selected == "👥 Customer & Supplier Master":
        party_master()

    elif selected == "🏭 Godown Management":
        godown_master()

    elif selected == "🧾 Sales Invoice":
        transaction_entry("Sales")

    elif selected == "🛒 Purchase Entry":
        transaction_entry("Purchase")

    elif selected == "🔄 Sales / Purchase Return":
        returns_module()

    elif selected == "📦 Stock Summary & Ledger":
        stock_module()

    elif selected == "📦 Barcode Quick Billing":
        barcode_billing()

    elif selected == "💰 Payment & Receipt":
        payment_receipt()

    elif selected == "🏦 Bank Accounts":
        bank_accounts()

    elif selected == "🧮 GST Reports":
        gst_reports()

    elif selected == "🏢 Company Profile":

        st.subheader("🏢 Company Settings")

        with st.form("company_form"):

            cname = st.text_input(
                "Business Registered Name",
                value=user["business_name"] or ""
            )

            addr = st.text_area(
                "Registered Address",
                value=user["business_address"] or ""
            )

            mob = st.text_input(
                "Mobile Phone Contact",
                value=user["mobile"] or ""
            )

            if st.form_submit_button(
                "Commit Profile Settings",
                type="primary"
            ):

                conn = db()

                conn.execute("""
                    UPDATE users
                    SET business_name=?, business_address=?, mobile=?
                    WHERE id=?
                """, (
                    cname,
                    addr,
                    mob,
                    st.session_state.user_id
                ))

                conn.commit()
                conn.close()

                st.success(
                    "Company Profile Updated Successfully!"
                )

                st.rerun()


# ================================================================
# START APPLICATION
# ================================================================

check_auto_login()

if st.session_state.user_id is None:
    login_page()
else:
    app()
