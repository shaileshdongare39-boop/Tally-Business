# ================================================================
# SD TALLY BUSINESS - PROFESSIONAL ALL-IN-ONE ERP
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
    page_title="SD TALLY BUSINESS ERP",
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
}

.main-title h1 {
    color: #38bdf8 !important;
    margin: 0;
    font-size: 2.2rem;
    font-weight: 800;
}

.main-title p {
    color: #94a3b8 !important;
    margin: 6px 0 0 0;
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

.small-note {
    color: #64748b;
    font-size: 0.85rem;
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
# COOKIE MANAGER (FIXED DUPLICATE KEY ISSUE)
# ================================================================

def get_cookie_manager():
    if COOKIES_OK:
        if "cookie_manager" not in st.session_state:
            st.session_state.cookie_manager = stx.CookieManager(key="sd_tally_cookie_mgr")
        return st.session_state.cookie_manager
    return None

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
        return True, "Password updated successfully! Please login with your new password."
    conn.close()
    return False, "Mobile number is not registered in the system."


def get_username_by_mobile(mobile):
    init_db()
    conn = db()
    row = conn.execute("SELECT username FROM users WHERE mobile=? AND active=1", (clean(mobile),)).fetchone()
    conn.close()
    if row:
        return True, f"Your Username is: **{row['username']}**"
    return False, "Mobile number is not registered in the system."


# ================================================================
# LOGIN PAGE
# ================================================================

def login_page():

    st.markdown("""
    <div class="main-title">
        <h1>🏢 SD TALLY BUSINESS ERP</h1>
        <p>Enterprise Combination of Tally Prime Accounting & Vyapar Smart Billing</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🔐 Sign In",
        "📝 Register Enterprise Account",
        "🔑 Credential Recovery"
    ])

    with tab1:

        st.subheader("Sign In To Account")

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
            "AUTHENTICATE & LOGIN",
            type="primary",
            use_container_width=True
        ):
            if login_user(username, password):
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.caption(
            "Username and password authentication is used. "
            "No paid OTP service is required."
        )

    with tab2:

        st.subheader("Create New Business Account")

        r_username = st.text_input(
            "Desired Username"
        )

        r_password = st.text_input(
            "Desired Password",
            type="password"
        )

        r_confirm = st.text_input(
            "Confirm Password",
            type="password"
        )

        r_name = st.text_input(
            "Owner Full Name"
        )

        r_mobile = st.text_input(
            "Mobile Number"
        )

        r_business = st.text_input(
            "Business / Company Name"
        )

        if st.button(
            "REGISTER ENTERPRISE ACCOUNT",
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
                    st.info(
                        "Your account is ready. "
                        "Use the Sign In tab."
                    )
                else:
                    st.error(message)

    with tab3:
        st.subheader("🔑 Credential Recovery")
        option = st.radio("Select Action", ["Find Username", "Reset Password"])

        if option == "Find Username":
            f_mobile = st.text_input("Enter Registered Mobile Number", key="find_user_mobile")
            if st.button("Fetch Username", type="primary"):
                if f_mobile:
                    ok, msg = get_username_by_mobile(f_mobile)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter mobile number.")

        elif option == "Reset Password":
            r_mobile = st.text_input("Enter Registered Mobile Number", key="reset_pass_mobile")
            new_pass = st.text_input("New Secure Password", type="password", key="reset_new_pass")
            confirm_pass = st.text_input("Confirm New Password", type="password", key="reset_confirm_pass")

            if st.button("Update Account Password", type="primary"):
                if not r_mobile:
                    st.warning("Please enter mobile number.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
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
        <b>🏢 Company:</b> {html.escape(user['business_name'] or "-")}<br><br>
        <b>🔑 Authority Level:</b> {html.escape(user['role'])}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.sidebar.button(
        "🚪 LOGOUT / EXIT SESSION",
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
# DASHBOARD MODULE
# ================================================================

def dashboard():

    st.subheader("📊 Business Overview & Analytics")

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
        "Net Sales Revenue",
        money(net_sales)
    )

    c2.metric(
        "Net Purchases",
        money(net_purchase)
    )

    c3.metric(
        "Gross Profit Margin",
        money(gross)
    )

    c4.metric(
        "Active Items / Parties",
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
# COMPANY PROFILE & SETTINGS
# ================================================================

def company_profile():

    st.subheader("🏢 Enterprise Profile Settings")

    user = get_user()
    settings = get_settings()

    with st.form("company_profile"):

        name = st.text_input(
            "Company Registered Name",
            value=user['business_name'] or ""
        )

        address = st.text_area(
            "Business Registered Address",
            value=user['business_address'] or ""
        )

        gstin = st.text_input(
            "GSTIN Registration Number",
            value=user['gstin'] or ""
        )

        phone = st.text_input(
            "Mobile Phone Contact",
            value=user['mobile'] or ""
        )

        email = st.text_input(
            "Official Business Email",
            value=(settings['email'] if settings else "")
        )

        prefix = st.text_input(
            "Invoice Prefix",
            value=(settings['invoice_prefix'] if settings else "INV")
        )

        upi = st.text_input(
            "Primary Business UPI ID",
            value=(settings['upi_id'] if settings else "")
        )

        payment_note = st.text_area(
            "Invoice Terms & Notes",
            value=(settings['payment_note'] if settings else "")
        )

        submitted = st.form_submit_button(
            "Commit Profile Settings",
            type="primary"
        )

    if submitted:

        conn = db()

        conn.execute("""
            UPDATE users
            SET business_name=?,
                business_address=?,
                gstin=?,
                mobile=?
            WHERE id=?
        """, (
            name,
            address,
            gstin,
            phone,
            st.session_state.user_id
        ))

        conn.execute("""
            UPDATE settings
            SET company_name=?,
                address=?,
                gstin=?,
                phone=?,
                email=?,
                invoice_prefix=?,
                upi_id=?,
                payment_note=?
            WHERE user_id=?
        """, (
            name,
            address,
            gstin,
            phone,
            email,
            prefix,
            upi,
            payment_note,
            st.session_state.user_id
        ))

        conn.commit()
        conn.close()

        audit(
            "UPDATE_COMPANY",
            "Company settings updated."
        )

        st.success(
            "Enterprise settings saved successfully."
        )
        st.rerun()


# ================================================================
# ITEM MASTER MODULE
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
                "HSN / SAC Tax Code"
            )

            unit = st.selectbox(
                "Measurement Unit",
                UNITS
            )

            gst = st.selectbox(
                "GST Tax Rate (%)",
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

            save = st.form_submit_button(
                "Save Product Master",
                type="primary"
            )

        if save:

            if not name.strip():
                st.error("Product Name is mandatory.")

            else:

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

                audit(
                    "ADD_ITEM",
                    name
                )

                st.success(
                    "Product Master saved successfully."
                )

    with tabs[1]:

        df = get_items()

        if df.empty:
            st.info("No products configured.")

        else:

            view = df[
                [
                    "id",
                    "name",
                    "sku",
                    "barcode",
                    "hsn",
                    "unit",
                    "gst_rate",
                    "sale_price",
                    "purchase_price",
                    "opening_stock",
                    "min_stock"
                ]
            ].copy()

            view["Current Stock"] = view["id"].apply(
                current_stock
            )

            st.dataframe(
                view,
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

                barcode = st.text_input(
                    "Barcode",
                    value=row["barcode"] or ""
                )

                hsn = st.text_input(
                    "HSN / SAC Code",
                    value=row["hsn"] or ""
                )

                unit = st.selectbox(
                    "Measurement Unit",
                    UNITS,
                    index=(
                        UNITS.index(row["unit"])
                        if row["unit"] in UNITS
                        else 0
                    )
                )

                gst = st.selectbox(
                    "GST Tax Rate (%)",
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

                minimum = st.number_input(
                    "Low Stock Threshold",
                    value=float(row["min_stock"])
                )

                save = st.form_submit_button(
                    "Update Product Master",
                    type="primary"
                )

            if save:

                conn = db()

                conn.execute("""
                    UPDATE items
                    SET name=?,
                        sku=?,
                        barcode=?,
                        hsn=?,
                        unit=?,
                        gst_rate=?,
                        sale_price=?,
                        purchase_price=?,
                        min_stock=?
                    WHERE id=? AND user_id=?
                """, (
                    name,
                    sku,
                    barcode,
                    hsn,
                    unit,
                    gst,
                    sale,
                    purchase,
                    minimum,
                    selected,
                    st.session_state.user_id
                ))

                conn.commit()
                conn.close()

                audit(
                    "EDIT_ITEM",
                    str(selected)
                )

                st.success(
                    "Product Master updated successfully."
                )
                st.rerun()


# ================================================================
# PARTY MASTER MODULE
# ================================================================

def party_master():

    st.subheader("👥 Customer & Supplier Ledger Directory")

    tabs = st.tabs([
        "Register Party Master",
        "Ledger Directory",
        "Update Party Details"
    ])

    with tabs[0]:

        with st.form("party_form"):

            name = st.text_input(
                "Party Legal Name *"
            )

            party_type = st.selectbox(
                "Account Contact Type",
                ["Customer", "Supplier"]
            )

            mobile = st.text_input(
                "Phone Number"
            )

            email = st.text_input(
                "Email Address"
            )

            gstin = st.text_input(
                "GSTIN Tax Number"
            )

            address = st.text_area(
                "Billing Address"
            )

            opening = st.number_input(
                "Opening Balance Amount",
                min_value=0.0,
                step=0.01
            )

            save = st.form_submit_button(
                "Save Party Master",
                type="primary"
            )

        if save:

            if not name.strip():
                st.error("Party Name is mandatory.")

            else:

                conn = db()

                conn.execute("""
                    INSERT INTO parties
                    (
                        user_id,
                        name,
                        party_type,
                        mobile,
                        email,
                        gstin,
                        address,
                        opening_balance
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    st.session_state.user_id,
                    name,
                    party_type,
                    mobile,
                    email,
                    gstin,
                    address,
                    opening
                ))

                conn.commit()
                conn.close()

                audit(
                    "ADD_PARTY",
                    name
                )

                st.success(
                    "Party Master created successfully."
                )

    with tabs[1]:

        df = get_parties()

        if df.empty:
            st.info("No party contacts registered.")

        else:
            st.dataframe(
                df[
                    [
                        "id",
                        "name",
                        "party_type",
                        "mobile",
                        "email",
                        "gstin",
                        "address",
                        "opening_balance"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

    with tabs[2]:

        df = get_parties()

        if not df.empty:

            selected = st.selectbox(
                "Select Party To Edit",
                df["id"].tolist(),
                format_func=lambda x:
                    df.loc[
                        df["id"] == x,
                        "name"
                    ].iloc[0]
            )

            row = df[df["id"] == selected].iloc[0]

            with st.form("edit_party"):

                name = st.text_input(
                    "Party Name",
                    value=row["name"]
                )

                party_type = st.selectbox(
                    "Party Type",
                    ["Customer", "Supplier"],
                    index=(
                        0
                        if row["party_type"] == "Customer"
                        else 1
                    )
                )

                mobile = st.text_input(
                    "Mobile Phone",
                    value=row["mobile"] or ""
                )

                email = st.text_input(
                    "Email Address",
                    value=row["email"] or ""
                )

                gstin = st.text_input(
                    "GSTIN Registration",
                    value=row["gstin"] or ""
                )

                address = st.text_area(
                    "Billing Address",
                    value=row["address"] or ""
                )

                save = st.form_submit_button(
                    "Update Party Contact",
                    type="primary"
                )

            if save:

                conn = db()

                conn.execute("""
                    UPDATE parties
                    SET name=?,
                        party_type=?,
                        mobile=?,
                        email=?,
                        gstin=?,
                        address=?
                    WHERE id=? AND user_id=?
                """, (
                    name,
                    party_type,
                    mobile,
                    email,
                    gstin,
                    address,
                    selected,
                    st.session_state.user_id
                ))

                conn.commit()
                conn.close()

                audit(
                    "EDIT_PARTY",
                    str(selected)
                )

                st.success(
                    "Party contact updated successfully."
                )

                st.rerun()


# ================================================================
# GODOWN MANAGEMENT MODULE
# ================================================================

def godown_master():

    st.subheader("🏭 Warehouse / Godown Management")

    with st.form("godown_form"):

        name = st.text_input(
            "Godown Name"
        )

        address = st.text_area(
            "Warehouse Location / Address"
        )

        save = st.form_submit_button(
            "Save Warehouse Master",
            type="primary"
        )

    if save:

        if not name.strip():
            st.error("Warehouse Name is mandatory.")

        else:

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

            audit(
                "ADD_GODOWN",
                name
            )

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
# TRANSACTION ENTRY VOUCHER MODULE
# ================================================================

def transaction_entry(voucher_type):

    st.subheader(
        f"🧾 {voucher_type} Voucher Creation Engine"
    )

    if voucher_type in ["Sales", "Sales Return"]:
        party_type = "Customer"
    elif voucher_type in ["Purchase", "Purchase Return"]:
        party_type = "Supplier"
    else:
        party_type = "Customer"

    parties = get_parties(party_type)
    items = get_items()

    if items.empty:
        st.warning(
            "Please configure Product Masters first."
        )
        return

    if parties.empty:
        st.warning(
            f"Please register a {party_type.lower()} contact first."
        )
        return

    col1, col2, col3 = st.columns(3)

    with col1:

        voucher_no = st.text_input(
            "Voucher Number",
            value=next_invoice_no()
            if voucher_type == "Sales"
            else ""
        )

    with col2:

        voucher_date = st.date_input(
            "Transaction Date",
            value=date.today()
        )

    with col3:

        payment_mode = st.selectbox(
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

    with c1:

        qty = st.number_input(
            "Quantity",
            min_value=0.01,
            value=1.0,
            step=1.0
        )

    with c2:

        default_rate = (
            float(item_row["sale_price"])
            if voucher_type == "Sales"
            else float(item_row["purchase_price"])
        )

        rate = st.number_input(
            "Unit Rate Price",
            min_value=0.0,
            value=default_rate,
            step=0.01
        )

    with c3:

        discount = st.number_input(
            "Discount %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5
        )

    gst_rate = st.selectbox(
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
        discount,
        gst_rate
    )

    st.info(
        f"Taxable Net: {money(line['taxable'])} | "
        f"CGST: {money(line['cgst'])} | "
        f"SGST: {money(line['sgst'])} | "
        f"Total: {money(line['total'])}"
    )

    if st.button(
        "➕ Add Product To Billing Cart"
    ):

        st.session_state.cart.append({
            "item_id": int(item_id),
            "item_name": item_row["name"],
            "qty": qty,
            "rate": rate,
            "discount": discount,
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

    st.markdown("### Voucher Invoice Lines")

    if st.session_state.cart:

        cart_df = pd.DataFrame(
            st.session_state.cart
        )

        st.dataframe(
            cart_df[
                [
                    "item_name",
                    "qty",
                    "rate",
                    "discount",
                    "taxable",
                    "gst_rate",
                    "cgst",
                    "sgst",
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

        taxable = sum(
            x["taxable"]
            for x in st.session_state.cart
        )

        cgst = sum(
            x["cgst"]
            for x in st.session_state.cart
        )

        sgst = sum(
            x["sgst"]
            for x in st.session_state.cart
        )

        st.markdown(
            f"""
            **Taxable Value:** {money(taxable)}  
            **CGST Value:** {money(cgst)}  
            **SGST Value:** {money(sgst)}  
            **Grand Invoice Total:** {money(total)}
            """
        )

        notes = st.text_area(
            "Transaction Narration / Notes"
        )

        c1, c2 = st.columns(2)

        with c1:

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
                    notes
                )

        with c2:

            if st.button(
                "🗑 Clear Cart Lines"
            ):

                st.session_state.cart = []
                st.rerun()


def save_voucher(
    voucher_type,
    voucher_no,
    voucher_date,
    party_id,
    party_name,
    payment_mode,
    notes
):

    if not st.session_state.cart:
        st.error(
            "Voucher cart must contain at least one item line."
        )
        return

    conn = db()

    duplicate = conn.execute("""
        SELECT id
        FROM vouchers
        WHERE user_id=?
        AND voucher_no=?
        AND voucher_type=?
    """, (
        st.session_state.user_id,
        voucher_no,
        voucher_type
    )).fetchone()

    if duplicate:
        conn.close()
        st.error(
            "Duplicate voucher number encountered."
        )
        return

    subtotal = sum(
        x["qty"] * x["rate"]
        for x in st.session_state.cart
    )

    discount = sum(
        x["discount"]
        for x in st.session_state.cart
    )

    taxable = sum(
        x["taxable"]
        for x in st.session_state.cart
    )

    cgst = sum(
        x["cgst"]
        for x in st.session_state.cart
    )

    sgst = sum(
        x["sgst"]
        for x in st.session_state.cart
    )

    igst = sum(
        x["igst"]
        for x in st.session_state.cart
    )

    total = sum(
        x["total"]
        for x in st.session_state.cart
    )

    cur = conn.cursor()

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
            subtotal,
            discount,
            taxable,
            cgst,
            sgst,
            igst,
            total,
            notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state.user_id,
        voucher_type,
        voucher_no,
        str(voucher_date),
        party_id,
        party_name,
        payment_mode,
        subtotal,
        discount,
        taxable,
        cgst,
        sgst,
        igst,
        total,
        notes,
        now_text()
    ))

    voucher_id = cur.lastrowid

    for line in st.session_state.cart:

        cur.execute("""
            INSERT INTO voucher_items
            (
                voucher_id,
                item_id,
                item_name,
                qty,
                rate,
                discount,
                taxable,
                gst_rate,
                cgst,
                sgst,
                igst,
                total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            voucher_id,
            line["item_id"],
            line["item_name"],
            line["qty"],
            line["rate"],
            line["discount"],
            line["taxable"],
            line["gst_rate"],
            line["cgst"],
            line["sgst"],
            line["igst"],
            line["total"]
        ))

        if voucher_type == "Sales":
            stock_qty = -abs(line["qty"])

        elif voucher_type == "Purchase":
            stock_qty = abs(line["qty"])

        elif voucher_type == "Sales Return":
            stock_qty = abs(line["qty"])

        elif voucher_type == "Purchase Return":
            stock_qty = -abs(line["qty"])

        else:
            stock_qty = 0

        if stock_qty != 0:

            cur.execute("""
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
                line["item_id"],
                voucher_id,
                str(voucher_date),
                voucher_type,
                stock_qty,
                line["rate"],
                voucher_no
            ))

    conn.commit()
    conn.close()

    # Ledger Posting
    if voucher_type == "Sales":
        debit_account = party_name if payment_mode == "Credit" else payment_mode
        add_ledger(
            debit_account,
            total,
            0,
            voucher_id,
            f"Sales Voucher {voucher_no}"
        )
        add_ledger(
            "Sales",
            0,
            taxable,
            voucher_id,
            f"Sales Voucher {voucher_no}"
        )

    elif voucher_type == "Purchase":
        credit_account = party_name if payment_mode == "Credit" else payment_mode
        add_ledger(
            "Purchase",
            taxable,
            0,
            voucher_id,
            f"Purchase Voucher {voucher_no}"
        )
        add_ledger(
            credit_account,
            0,
            total,
            voucher_id,
            f"Purchase Voucher {voucher_no}"
        )

    audit(
        "ADD_VOUCHER",
        f"{voucher_type} {voucher_no}"
    )

    st.session_state.cart = []

    st.success(
        f"{voucher_type} Voucher {voucher_no} committed successfully."
    )


# ================================================================
# RETURNS MODULE
# ================================================================

def returns_module():

    st.subheader("🔄 Credit Notes & Debit Notes (Returns)")

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
# STOCK MODULE
# ================================================================

def stock_module():

    st.subheader("📦 Stock Valuation Summary & Inventory Ledger")

    df = get_items()

    if df.empty:
        st.info("No product items available.")
        return

    rows = []

    for _, row in df.iterrows():

        stock = current_stock(
            int(row["id"])
        )

        rows.append({
            "ID": row["id"],
            "Product": row["name"],
            "SKU": row["sku"],
            "Unit": row["unit"],
            "GST %": row["gst_rate"],
            "Selling Rate": row["sale_price"],
            "Purchase Rate": row["purchase_price"],
            "Current Stock": stock,
            "Low Threshold": row["min_stock"],
            "Status":
                "LOW STOCK ALERT"
                if stock <= row["min_stock"]
                else "OPTIMAL"
        })

    stock_df = pd.DataFrame(rows)

    st.dataframe(
        stock_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Product Stock Ledger History")

    item_id = st.selectbox(
        "Select Product Item",
        df["id"].tolist(),
        format_func=lambda x:
            df.loc[
                df["id"] == x,
                "name"
            ].iloc[0]
    )

    conn = db()

    ledger = pd.read_sql_query(
        """
        SELECT
            txn_date,
            txn_type,
            qty,
            rate,
            remarks
        FROM stock_transactions
        WHERE user_id=? AND item_id=?
        ORDER BY txn_date DESC, id DESC
        """,
        conn,
        params=(
            st.session_state.user_id,
            item_id
        )
    )

    conn.close()

    st.dataframe(
        ledger,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# VOUCHER REGISTER
# ================================================================

def voucher_register():

    st.subheader("🔍 Voucher Search, Audit & Revocation")

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            id,
            voucher_type,
            voucher_no,
            voucher_date,
            party_name,
            payment_mode,
            taxable,
            cgst,
            sgst,
            total
        FROM vouchers
        WHERE user_id=?
        ORDER BY id DESC
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    conn.close()

    if df.empty:
        st.info("No vouchers committed.")
        return

    search = st.text_input(
        "Search Voucher / Party Ledger"
    )

    if search:
        mask = (
            df["voucher_no"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
            |
            df["party_name"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
        )

        df = df[mask]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if df.empty:
        return

    selected = st.selectbox(
        "Select Voucher Record ID",
        df["id"].tolist()
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "🗑 Revoke / Delete Voucher"
        ):

            if not user_is_owner():
                st.error(
                    "Only Owner profile can delete vouchers."
                )
            else:

                delete_voucher(
                    int(selected)
                )

    with c2:

        if st.button(
            "👁 View Voucher Breakdown"
        ):

            show_voucher(
                int(selected)
            )


def delete_voucher(voucher_id):

    conn = db()

    voucher = conn.execute("""
        SELECT voucher_type, voucher_no
        FROM vouchers
        WHERE id=? AND user_id=?
    """, (
        voucher_id,
        st.session_state.user_id
    )).fetchone()

    if not voucher:
        conn.close()
        st.error("Voucher not located.")
        return

    conn.execute("""
        DELETE FROM voucher_items
        WHERE voucher_id=?
    """, (voucher_id,))

    conn.execute("""
        DELETE FROM stock_transactions
        WHERE voucher_id=?
    """, (voucher_id,))

    conn.execute("""
        DELETE FROM ledger_entries
        WHERE voucher_id=?
    """, (voucher_id,))

    conn.execute("""
        DELETE FROM vouchers
        WHERE id=? AND user_id=?
    """, (
        voucher_id,
        st.session_state.user_id
    ))

    conn.commit()
    conn.close()

    audit(
        "DELETE_VOUCHER",
        f"{voucher['voucher_type']} {voucher['voucher_no']}"
    )

    st.success(
        "Voucher revoked successfully."
    )

    st.rerun()


def show_voucher(voucher_id):

    conn = db()

    voucher = pd.read_sql_query(
        """
        SELECT *
        FROM vouchers
        WHERE id=? AND user_id=?
        """,
        conn,
        params=(
            voucher_id,
            st.session_state.user_id
        )
    )

    lines = pd.read_sql_query(
        """
        SELECT *
        FROM voucher_items
        WHERE voucher_id=?
        """,
        conn,
        params=(voucher_id,)
    )

    conn.close()

    if voucher.empty:
        return

    v = voucher.iloc[0]

    st.markdown(
        f"""
        ### {v['voucher_type']}
        **Voucher No:** {v['voucher_no']}  
        **Date:** {v['voucher_date']}  
        **Party:** {v['party_name']}  
        **Payment Mode:** {v['payment_mode']}  
        **Grand Total:** {money(v['total'])}
        """
    )

    st.dataframe(
        lines,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# DAY BOOK MODULE
# ================================================================

def day_book():

    st.subheader("📅 Daily Day-Book Summary")

    start = st.date_input(
        "From Date",
        value=date.today()
    )

    end = st.date_input(
        "To Date",
        value=date.today()
    )

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            voucher_date,
            voucher_type,
            voucher_no,
            party_name,
            payment_mode,
            total
        FROM vouchers
        WHERE user_id=?
        AND voucher_date BETWEEN ? AND ?
        ORDER BY voucher_date DESC, id DESC
        """,
        conn,
        params=(
            st.session_state.user_id,
            str(start),
            str(end)
        )
    )

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# PARTY REPORTS & LEDGERS
# ================================================================

def party_reports():

    st.subheader("👥 Party Ledger Statements & Outstanding")

    parties = get_parties()

    if parties.empty:
        st.info("No parties configured.")
        return

    party_id = st.selectbox(
        "Select Party Contact",
        parties["id"].tolist(),
        format_func=lambda x:
            parties.loc[
                parties["id"] == x,
                "name"
            ].iloc[0]
    )

    party = parties[
        parties["id"] == party_id
    ].iloc[0]

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            voucher_date,
            voucher_type,
            voucher_no,
            payment_mode,
            total
        FROM vouchers
        WHERE user_id=?
        AND party_id=?
        ORDER BY voucher_date DESC
        """,
        conn,
        params=(
            st.session_state.user_id,
            party_id
        )
    )

    conn.close()

    st.write(
        f"**Account Statement For:** {party['name']}"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    sales_credit = df[
        (df["voucher_type"] == "Sales")
        &
        (df["payment_mode"] == "Credit")
    ]["total"].sum()

    purchase_credit = df[
        (df["voucher_type"] == "Purchase")
        &
        (df["payment_mode"] == "Credit")
    ]["total"].sum()

    c1, c2 = st.columns(2)

    c1.metric(
        "Receivable Credit Balance",
        money(sales_credit)
    )

    c2.metric(
        "Payable Credit Balance",
        money(purchase_credit)
    )


# ================================================================
# GST COMPLIANCE REPORTING
# ================================================================

def gst_reports():

    st.subheader("🧮 GST Compliance & Tax Reports")

    start = st.date_input(
        "Start Date",
        value=date.today().replace(day=1)
    )

    end = st.date_input(
        "End Date",
        value=date.today()
    )

    conn = db()

    sales = pd.read_sql_query(
        """
        SELECT
            voucher_no,
            voucher_date,
            party_name,
            taxable,
            cgst,
            sgst,
            igst,
            total
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Sales'
        AND voucher_date BETWEEN ? AND ?
        """,
        conn,
        params=(
            st.session_state.user_id,
            str(start),
            str(end)
        )
    )

    purchases = pd.read_sql_query(
        """
        SELECT
            voucher_no,
            voucher_date,
            party_name,
            taxable,
            cgst,
            sgst,
            igst,
            total
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Purchase'
        AND voucher_date BETWEEN ? AND ?
        """,
        conn,
        params=(
            st.session_state.user_id,
            str(start),
            str(end)
        )
    )

    conn.close()

    st.markdown("### GSTR-1 Sales Summary")

    st.dataframe(
        sales,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### GSTR-2 Purchase / ITC Summary")

    st.dataframe(
        purchases,
        use_container_width=True,
        hide_index=True
    )

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        sales.to_excel(
            writer,
            index=False,
            sheet_name="GSTR1"
        )

        purchases.to_excel(
            writer,
            index=False,
            sheet_name="Purchase_ITC"
        )

    st.download_button(
        "📥 Download GST Excel Report",
        data=output.getvalue(),
        file_name="GST_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# ================================================================
# TRIAL BALANCE & LEDGER MODULE
# ================================================================

def trial_balance():

    st.subheader("📒 Ledger & Trial Balance")

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            account_name,
            SUM(debit) AS Debit,
            SUM(credit) AS Credit
        FROM ledger_entries
        WHERE user_id=?
        GROUP BY account_name
        ORDER BY account_name
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    conn.close()

    if df.empty:
        st.info(
            "No accounting ledger entries available."
        )
        return

    df["Difference"] = (
        df["Debit"] - df["Credit"]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.metric(
        "Total Debit Ledger",
        money(df["Debit"].sum())
    )

    st.metric(
        "Total Credit Ledger",
        money(df["Credit"].sum())
    )


# ================================================================
# PROFIT & LOSS STATEMENT
# ================================================================

def profit_loss():

    st.subheader("📈 Profit & Loss Statement")

    conn = db()

    sales = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Sales'
    """, (
        st.session_state.user_id,
    )).fetchone()[0]

    purchases = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Purchase'
    """, (
        st.session_state.user_id,
    )).fetchone()[0]

    sales_return = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Sales Return'
    """, (
        st.session_state.user_id,
    )).fetchone()[0]

    purchase_return = conn.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Purchase Return'
    """, (
        st.session_state.user_id,
    )).fetchone()[0]

    conn.close()

    net_sales = sales - sales_return
    net_purchase = purchases - purchase_return
    gross_profit = net_sales - net_purchase

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Net Sales",
        money(net_sales)
    )

    c2.metric(
        "Net Purchase",
        money(net_purchase)
    )

    c3.metric(
        "Gross Profit / Loss Margin",
        money(gross_profit)
    )

    df = pd.DataFrame({
        "Particular": [
            "Net Revenue",
            "Net Purchases",
            "Gross Profit / Loss"
        ],
        "Amount": [
            net_sales,
            net_purchase,
            gross_profit
        ]
    })

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# BALANCE SHEET
# ================================================================

def balance_sheet():

    st.subheader("📋 Balance Sheet")

    conn = db()

    cash_bank = conn.execute("""
        SELECT
            COALESCE(SUM(total),0)
        FROM vouchers
        WHERE user_id=?
        AND payment_mode IN ('Cash','Bank','UPI')
        AND voucher_type='Sales'
    """, (
        st.session_state.user_id,
    )).fetchone()[0]

    conn.close()

    st.metric(
        "Recorded Cash / Bank Balance",
        money(cash_bank)
    )


# ================================================================
# PAYMENT & RECEIPT VOUCHERS
# ================================================================

def payment_receipt():

    st.subheader("💰 Payment & Receipt Transactions")

    typ = st.selectbox(
        "Transaction Entry Type",
        ["Payment", "Receipt"]
    )

    parties = get_parties()

    party_name = ""

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

        party_name = parties.loc[
            parties["id"] == party_id,
            "name"
        ].iloc[0]

    amount = st.number_input(
        "Transaction Amount",
        min_value=0.01,
        step=0.01
    )

    mode = st.selectbox(
        "Settlement Mode",
        PAYMENT_MODES
    )

    reference = st.text_input(
        "UTR / Ref Number"
    )

    narration = st.text_area(
        "Narration / Notes"
    )

    if st.button(
        f"Commit {typ} Voucher",
        type="primary"
    ):

        conn = db()

        voucher_no = next_invoice_no()

        cur = conn.cursor()

        cur.execute("""
            INSERT INTO vouchers
            (
                user_id,
                voucher_type,
                voucher_no,
                voucher_date,
                party_name,
                payment_mode,
                total,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.user_id,
            typ,
            voucher_no,
            today_text(),
            party_name,
            mode,
            amount,
            narration,
            now_text()
        ))

        vid = cur.lastrowid

        conn.commit()
        conn.close()

        if typ == "Payment":

            add_ledger(
                party_name or "Payment",
                0,
                amount,
                vid,
                narration
            )

        else:

            add_ledger(
                party_name or "Receipt",
                amount,
                0,
                vid,
                narration
            )

        audit(
            "ADD_PAYMENT_RECEIPT",
            voucher_no
        )

        st.success(
            f"{typ} Voucher committed successfully."
        )


# ================================================================
# BANK ACCOUNT MANAGEMENT
# ================================================================

def bank_accounts():

    st.subheader("🏦 Bank Account Management")

    with st.form("bank_form"):

        bank_name = st.text_input(
            "Bank Institution Name"
        )

        account = st.text_input(
            "Account Number"
        )

        ifsc = st.text_input(
            "IFSC Code"
        )

        branch = st.text_input(
            "Branch Location"
        )

        opening = st.number_input(
            "Opening Balance Amount",
            min_value=0.0,
            step=0.01
        )

        save = st.form_submit_button(
            "Save Bank Account",
            type="primary"
        )

    if save:

        conn = db()

        conn.execute("""
            INSERT INTO bank_accounts
            (
                user_id,
                bank_name,
                account_no,
                ifsc,
                branch,
                opening_balance
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.user_id,
            bank_name,
            account,
            ifsc,
            branch,
            opening
        ))

        conn.commit()
        conn.close()

        audit(
            "ADD_BANK_ACCOUNT",
            bank_name
        )

        st.success(
            "Bank account configured successfully."
        )

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            id,
            bank_name,
            account_no,
            ifsc,
            branch,
            opening_balance
        FROM bank_accounts
        WHERE user_id=? AND active=1
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
# REPORT EXPORT MODULE
# ================================================================

def report_export():

    st.subheader("📤 Data Export Engine (Excel & CSV)")

    conn = db()

    vouchers = pd.read_sql_query(
        """
        SELECT *
        FROM vouchers
        WHERE user_id=?
        ORDER BY id DESC
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    items = pd.read_sql_query(
        """
        SELECT *
        FROM items
        WHERE user_id=?
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    parties = pd.read_sql_query(
        """
        SELECT *
        FROM parties
        WHERE user_id=?
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    conn.close()

    st.markdown("### Voucher Transaction Dataset")

    st.dataframe(
        vouchers,
        use_container_width=True,
        hide_index=True
    )

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        vouchers.to_excel(
            writer,
            index=False,
            sheet_name="Vouchers"
        )

        items.to_excel(
            writer,
            index=False,
            sheet_name="Items"
        )

        parties.to_excel(
            writer,
            index=False,
            sheet_name="Parties"
        )

    st.download_button(
        "📥 Download Enterprise Excel Backup",
        data=output.getvalue(),
        file_name="SD_TALLY_COMPLETE_REPORT.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# ================================================================
# DATABASE BACKUP MODULE
# ================================================================

def backup_restore():

    st.subheader("☁️ Cloud Database Backup")

    if os.path.exists(DB_FILE):

        with open(
            DB_FILE,
            "rb"
        ) as f:

            st.download_button(
                "📥 Download SQL Database File",
                data=f.read(),
                file_name="sd_tally_business_backup.db",
                mime="application/octet-stream"
            )


# ================================================================
# USER & PERMISSION MANAGEMENT
# ================================================================

def user_management():

    st.subheader("🔐 Staff & Authority Permissions")

    if not user_is_owner():

        st.error(
            "Only Owner profile can configure staff permissions."
        )
        return

    with st.form("staff_form"):

        username = st.text_input(
            "Staff Username"
        )

        password = st.text_input(
            "Staff Password",
            type="password"
        )

        name = st.text_input(
            "Staff Full Name"
        )

        mobile = st.text_input(
            "Mobile Phone"
        )

        save = st.form_submit_button(
            "Create Staff Account",
            type="primary"
        )

    owner_user = get_user()

    if save:

        if len(password) < 6:
            st.error(
                "Password must be at least 6 characters."
            )

        else:

            conn = db()

            try:

                conn.execute("""
                    INSERT INTO users
                    (
                        username,
                        password_hash,
                        name,
                        mobile,
                        role,
                        business_name,
                        business_address,
                        gstin,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, 'Staff',
                            ?, ?, ?, ?)
                """, (
                    username.lower().strip(),
                    hash_password(password),
                    name,
                    mobile,
                    owner_user['business_name'],
                    owner_user['business_address'],
                    owner_user['gstin'],
                    now_text()
                ))

                conn.commit()

                st.success(
                    "Staff account registered successfully."
                )

            except sqlite3.IntegrityError:

                st.error(
                    "Username already exists."
                )

            finally:
                conn.close()

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            id,
            username,
            name,
            mobile,
            role,
            active,
            created_at
        FROM users
        WHERE business_name=?
        ORDER BY id
        """,
        conn,
        params=(owner_user['business_name'],)
    )

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ================================================================
# THERMAL RECEIPT PRINTING
# ================================================================

def thermal_receipt():

    st.subheader("🖨️ Thermal Receipt Printing")

    conn = db()

    df = pd.read_sql_query(
        """
        SELECT
            id,
            voucher_no,
            voucher_date,
            party_name,
            total
        FROM vouchers
        WHERE user_id=?
        AND voucher_type='Sales'
        ORDER BY id DESC
        """,
        conn,
        params=(st.session_state.user_id,)
    )

    conn.close()

    if df.empty:
        st.info(
            "No sales invoices committed."
        )
        return

    selected = st.selectbox(
        "Select Sales Invoice",
        df["id"].tolist(),
        format_func=lambda x:
            df.loc[
                df["id"] == x,
                "voucher_no"
            ].iloc[0]
    )

    row = df[
        df["id"] == selected
    ].iloc[0]

    user = get_user()

    st.markdown(
        f"""
        <div style="
            width:280px;
            margin:auto;
            background:white;
            color:black;
            padding:15px;
            font-family:monospace;
            border:1px dashed #222;
        ">
        <center>
        <h3>{html.escape(user['business_name'] or 'Business')}</h3>
        <div>TAX INVOICE</div>
        </center>
        <hr>
        Invoice: {row['voucher_no']}<br>
        Date: {row['voucher_date']}<br>
        Customer: {html.escape(str(row['party_name'] or ''))}
        <hr>
        <h3>Total: {money(row['total'])}</h3>
        <center>Thank You</center>
        </div>
        """,
        unsafe_allow_html=True
    )


# ================================================================
# BARCODE QUICK BILLING
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
            WHERE user_id=?
            AND barcode=?
            AND active=1
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
                "Billing Quantity",
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
                    "discount": 0,
                    "taxable": line["taxable"],
                    "gst_rate": row['gst_rate'],
                    "cgst": line["cgst"],
                    "sgst": line["sgst"],
                    "igst": 0,
                    "total": line["total"]
                })

                st.success(
                    "Added to cart."
                )

        else:

            st.error(
                "Barcode not found."
            )

    if st.session_state.cart:

        st.dataframe(
            pd.DataFrame(
                st.session_state.cart
            ),
            use_container_width=True,
            hide_index=True
        )


# ================================================================
# MY ACCOUNT / PROFILE
# ================================================================

def account_page():

    st.subheader("👤 Account Profile Details")

    user = get_user()

    st.write(
        f"**Username:** {user['username']}"
    )

    st.write(
        f"**Owner Name:** {user['name']}"
    )

    st.write(
        f"**Mobile Phone:** {user['mobile']}"
    )

    st.write(
        f"**Role:** {user['role']}"
    )

    st.markdown("---")

    st.subheader(
        "Change Account Password"
    )

    old = st.text_input(
        "Current Password",
        type="password"
    )

    new = st.text_input(
        "New Password",
        type="password"
    )

    confirm = st.text_input(
        "Confirm New Password",
        type="password"
    )

    if st.button(
        "Update Account Password",
        type="primary"
    ):

        if len(new) < 6:
            st.error(
                "New password must be at least 6 characters."
            )
            return

        if new != confirm:
            st.error(
                "Passwords do not match."
            )
            return

        conn = db()

        row = conn.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id=?
            """,
            (st.session_state.user_id,)
        ).fetchone()

        if not verify_password(
            old,
            row["password_hash"]
        ):

            st.error(
                "Current password is incorrect."
            )

        else:

            conn.execute("""
                UPDATE users
                SET password_hash=?
                WHERE id=?
            """, (
                hash_password(new),
                st.session_state.user_id
            ))

            conn.commit()

            st.success(
                "Password updated successfully."
            )

        conn.close()


# ================================================================
# NAVIGATION & CATEGORY BOARD
# ================================================================

def app():

    sidebar()

    user = get_user()

    st.markdown(
        f"""
        <div class="main-title">
            <h1>{html.escape(user['business_name'] or "SD TALLY BUSINESS ERP")}</h1>
            <p>
                Enterprise Business ERP |
                Active User: {html.escape(user['username'])} |
                Authority Level: {html.escape(user['role'])}
            </p>
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
        "👥 Party Ledger & Outstanding",
        "📅 Day Book",
        "📒 Ledger & Trial Balance",
        "🧮 GST Reports",
        "📈 Profit & Loss",
        "📋 Balance Sheet",
        "🔍 Voucher Search / Edit / Delete",
        "🖨️ Thermal Receipt",
        "📤 Excel / CSV Export",
        "☁️ Database Backup",
        "🏢 Company Profile",
        "🔐 User Management",
        "👤 My Account"
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

    elif selected == "👥 Party Ledger & Outstanding":
        party_reports()

    elif selected == "📅 Day Book":
        day_book()

    elif selected == "📒 Ledger & Trial Balance":
        trial_balance()

    elif selected == "🧮 GST Reports":
        gst_reports()

    elif selected == "📈 Profit & Loss":
        profit_loss()

    elif selected == "📋 Balance Sheet":
        balance_sheet()

    elif selected == "🔍 Voucher Search / Edit / Delete":
        voucher_register()

    elif selected == "🖨️ Thermal Receipt":
        thermal_receipt()

    elif selected == "📤 Excel / CSV Export":
        report_export()

    elif selected == "☁️ Database Backup":
        backup_restore()

    elif selected == "🏢 Company Profile":
        company_profile()

    elif selected == "🔐 User Management":
        user_management()

    elif selected == "👤 My Account":
        account_page()


# ================================================================
# START APPLICATION
# ================================================================

check_auto_login()

if st.session_state.user_id is None:
    login_page()
else:
    app()
