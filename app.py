import streamlit as st
import sqlite3
import io
import hashlib
import secrets
from datetime import date, datetime, timedelta

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


# ============================================================
# SD TALLY BUSINESS
# PROFESSIONAL ALL-IN-ONE ERP
# CORRECTED PART 1
# ============================================================

APP_NAME = "SD TALLY BUSINESS"
APP_VERSION = "4.0.1"
DB_FILE = "sd_tally_business_enterprise.db"


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
    }

    .main-header {
        background: linear-gradient(
            135deg,
            #0f172a,
            #1e293b
        );
        padding: 22px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
    }

    .main-header h1 {
        margin: 0;
        color: #38bdf8 !important;
    }

    .main-header p {
        margin-top: 6px;
        color: #cbd5e1;
    }

    .card {
        background: white;
        padding: 16px;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 14px;
    }

    .success-box {
        background: #ecfdf5;
        border: 1px solid #10b981;
        padding: 12px;
        border-radius: 10px;
    }

    .warning-box {
        background: #fffbeb;
        border: 1px solid #f59e0b;
        padding: 12px;
        border-radius: 10px;
    }

    .danger-box {
        background: #fef2f2;
        border: 1px solid #ef4444;
        padding: 12px;
        border-radius: 10px;
    }

    .stButton > button {
        min-height: 42px;
        font-weight: 700;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATABASE
# ============================================================

def db():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


def q(sql, params=()):
    if pd is None:
        raise RuntimeError(
            "pandas is required. "
            "Install using: pip install pandas"
        )

    con = db()

    try:
        return pd.read_sql_query(
            sql,
            con,
            params=params
        )
    finally:
        con.close()


def exec_sql(sql, params=()):
    con = db()

    try:
        cur = con.cursor()
        cur.execute(sql, params)
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def exec_many(sql, rows):
    con = db()

    try:
        cur = con.cursor()
        cur.executemany(sql, rows)
        con.commit()
    finally:
        con.close()


# ============================================================
# SAFE DATABASE MIGRATION
# ============================================================

def add_column_if_missing(
    con,
    table,
    column,
    definition
):
    cur = con.cursor()

    cur.execute(
        f"PRAGMA table_info({table})"
    )

    columns = [
        row[1]
        for row in cur.fetchall()
    ]

    if column not in columns:

        cur.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {definition}
            """
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    con = db()
    c = con.cursor()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            mobile TEXT PRIMARY KEY,
            name TEXT,
            business_name TEXT,
            business_address TEXT,
            gstin TEXT,
            state_code TEXT,
            reg_date TEXT,
            trial_end_date TEXT,
            is_paid INTEGER DEFAULT 0,
            paid_till TEXT,
            role TEXT DEFAULT 'Owner',
            pin_hash TEXT,
            active INTEGER DEFAULT 1
        )
        """
    )

    # Old DB compatibility
    user_columns = [
        ("name", "TEXT"),
        ("business_name", "TEXT"),
        ("business_address", "TEXT"),
        ("gstin", "TEXT"),
        ("state_code", "TEXT"),
        ("reg_date", "TEXT"),
        ("trial_end_date", "TEXT"),
        ("is_paid", "INTEGER DEFAULT 0"),
        ("paid_till", "TEXT"),
        ("role", "TEXT DEFAULT 'Owner'"),
        ("pin_hash", "TEXT"),
        ("active", "INTEGER DEFAULT 1")
    ]

    for column, definition in user_columns:

        add_column_if_missing(
            con,
            "users",
            column,
            definition
        )


    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS settings(
            user_mobile TEXT PRIMARY KEY,
            financial_year TEXT,
            invoice_prefix TEXT DEFAULT 'INV',
            purchase_prefix TEXT DEFAULT 'PUR',
            default_gst REAL DEFAULT 18,
            company_state_code TEXT,
            invoice_terms TEXT,
            currency TEXT DEFAULT 'INR'
        )
        """
    )


    # --------------------------------------------------------
    # ACCOUNTS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            name TEXT,
            group_name TEXT,
            account_type TEXT,
            opening_debit REAL DEFAULT 0,
            opening_credit REAL DEFAULT 0,
            active INTEGER DEFAULT 1,
            UNIQUE(user_mobile, name)
        )
        """
    )


    # --------------------------------------------------------
    # PARTIES
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS parties(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            party_name TEXT,
            gstin TEXT,
            mobile TEXT,
            email TEXT,
            address TEXT,
            state_code TEXT,
            party_type TEXT,
            opening_balance REAL DEFAULT 0,
            credit_limit REAL DEFAULT 0,
            credit_days INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
        """
    )


    # --------------------------------------------------------
    # GODOWNS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS godowns(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            godown_name TEXT,
            address TEXT,
            active INTEGER DEFAULT 1,
            UNIQUE(user_mobile, godown_name)
        )
        """
    )


    # --------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            item_name TEXT,
            sku TEXT,
            barcode TEXT,
            hsn_sac TEXT,
            unit TEXT DEFAULT 'PCS',
            godown TEXT DEFAULT 'Main Store',
            sale_price REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            opening_qty REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            batch_enabled INTEGER DEFAULT 0,
            expiry_enabled INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            UNIQUE(user_mobile, item_name)
        )
        """
    )


    # --------------------------------------------------------
    # VOUCHERS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS vouchers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            vdate TEXT,
            party_id INTEGER,
            party_name TEXT,
            payment_mode TEXT DEFAULT 'Credit',
            narration TEXT,
            taxable REAL DEFAULT 0,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            round_off REAL DEFAULT 0,
            total REAL DEFAULT 0,
            reference_no TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Posted',
            created_at TEXT
        )
        """
    )


    # --------------------------------------------------------
    # VOUCHER ITEMS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS voucher_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_id INTEGER,
            item_id INTEGER,
            item_name TEXT,
            unit TEXT,
            hsn_sac TEXT,
            qty REAL,
            rate REAL,
            discount REAL DEFAULT 0,
            taxable REAL,
            gst_rate REAL,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            total REAL,
            godown TEXT,
            batch_no TEXT,
            expiry_date TEXT
        )
        """
    )


    # --------------------------------------------------------
    # JOURNAL
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS journal(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            voucher_id INTEGER,
            vdate TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            account_name TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            narration TEXT
        )
        """
    )


    # --------------------------------------------------------
    # STOCK
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_moves(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            vdate TEXT,
            voucher_id INTEGER,
            item_id INTEGER,
            item_name TEXT,
            godown TEXT,
            batch_no TEXT,
            expiry_date TEXT,
            move_type TEXT,
            qty_in REAL DEFAULT 0,
            qty_out REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            reference_no TEXT
        )
        """
    )


    # --------------------------------------------------------
    # RECEIPTS / PAYMENTS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts_payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            vdate TEXT,
            txn_type TEXT,
            voucher_no TEXT,
            party_id INTEGER,
            party_name TEXT,
            account_name TEXT,
            amount REAL,
            mode TEXT,
            reference TEXT,
            narration TEXT
        )
        """
    )


    # --------------------------------------------------------
    # ALLOCATIONS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS allocations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            txn_id INTEGER,
            invoice_id INTEGER,
            amount REAL
        )
        """
    )


    # --------------------------------------------------------
    # EXPENSES
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            vdate TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            mode TEXT
        )
        """
    )


    # --------------------------------------------------------
    # RETURNS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS returns(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            vdate TEXT,
            return_type TEXT,
            reference_no TEXT,
            party_name TEXT,
            item_id INTEGER,
            item_name TEXT,
            qty REAL,
            taxable REAL,
            gst REAL,
            total REAL,
            reason TEXT
        )
        """
    )


    # --------------------------------------------------------
    # BANK ACCOUNTS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS bank_accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            bank_name TEXT,
            account_no TEXT,
            ifsc TEXT,
            branch TEXT,
            opening_balance REAL DEFAULT 0,
            active INTEGER DEFAULT 1
        )
        """
    )


    # --------------------------------------------------------
    # BANK STATEMENT
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS bank_statement(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            txn_date TEXT,
            description TEXT,
            reference TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            reconciled INTEGER DEFAULT 0,
            imported_file TEXT
        )
        """
    )


    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            created_at TEXT,
            action TEXT,
            entity TEXT,
            record_id INTEGER,
            details TEXT
        )
        """
    )


    # --------------------------------------------------------
    # BRANDING
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS branding(
            user_mobile TEXT PRIMARY KEY,
            logo_b64 TEXT,
            signature_b64 TEXT,
            bank_details TEXT
        )
        """
    )


    con.commit()
    con.close()


init_db()


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def today():
    return date.today().isoformat()


def money(value):
    try:
        return f"₹ {float(value or 0):,.2f}"
    except Exception:
        return "₹ 0.00"


def sha(value):
    return hashlib.sha256(
        str(value).encode("utf-8")
    ).hexdigest()


def current_user():
    return st.session_state.get(
        "user_mobile"
    )


def user_row():

    mobile = current_user()

    if not mobile:
        return None

    data = q(
        """
        SELECT *
        FROM users
        WHERE mobile=?
        AND active=1
        LIMIT 1
        """,
        (mobile,)
    )

    if data.empty:
        return None

    return data.iloc[0].to_dict()


def settings_row():

    mobile = current_user()

    if not mobile:
        return {}

    data = q(
        """
        SELECT *
        FROM settings
        WHERE user_mobile=?
        LIMIT 1
        """,
        (mobile,)
    )

    if data.empty:
        return {}

    return data.iloc[0].to_dict()


def log(
    action,
    entity="",
    record_id=None,
    details=""
):

    mobile = current_user()

    if not mobile:
        return

    exec_sql(
        """
        INSERT INTO audit_log(
            user_mobile,
            created_at,
            action,
            entity,
            record_id,
            details
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            mobile,
            now(),
            action,
            entity,
            record_id,
            details
        )
    )


def fy_for(date_string):

    d = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    ).date()

    if d.month >= 4:
        year = d.year
    else:
        year = d.year - 1

    return (
        f"{year}-{str(year + 1)[-2:]}"
    )


# ============================================================
# DEFAULT ACCOUNTS
# ============================================================

def ensure_accounts():

    if not current_user():
        return

    defaults = [

        ("Cash", "Cash", "Asset"),
        ("Bank", "Bank", "Asset"),
        ("Sales", "Sales", "Income"),
        ("Purchase", "Purchase", "Expense"),

        ("CGST Output", "GST", "Liability"),
        ("SGST Output", "GST", "Liability"),
        ("IGST Output", "GST", "Liability"),

        ("CGST Input", "GST", "Asset"),
        ("SGST Input", "GST", "Asset"),
        ("IGST Input", "GST", "Asset"),

        ("Capital", "Capital", "Equity"),

        (
            "Discount Allowed",
            "Indirect Expense",
            "Expense"
        ),

        (
            "Discount Received",
            "Indirect Income",
            "Income"
        ),

        (
            "Round Off",
            "Indirect Expense",
            "Expense"
        ),

        (
            "Receivable",
            "Sundry Debtors",
            "Asset"
        ),

        (
            "Payable",
            "Sundry Creditors",
            "Liability"
        )
    ]

    for name, group_name, account_type in defaults:

        exec_sql(
            """
            INSERT OR IGNORE INTO accounts(
                user_mobile,
                name,
                group_name,
                account_type
            )
            VALUES(?,?,?,?)
            """,
            (
                current_user(),
                name,
                group_name,
                account_type
            )
        )


# ============================================================
# SESSION
# ============================================================

if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None

if "otp" not in st.session_state:
    st.session_state.otp = None

if "cart" not in st.session_state:
    st.session_state.cart = []

if "invoice_draft" not in st.session_state:
    st.session_state.invoice_draft = []

if "pur_rows" not in st.session_state:
    st.session_state.pur_rows = []


# ============================================================
# LOGIN
# ============================================================

if not current_user():

    st.markdown(
        """
        <div class="main-header">
            <h1>🏢 SD TALLY BUSINESS</h1>
            <p>
                Professional All-in-One
                Accounting & ERP
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    mobile = st.text_input(
        "📱 Mobile Number",
        max_chars=10
    )

    if st.button("Send OTP"):

        if (
            mobile.isdigit()
            and len(mobile) == 10
        ):

            st.session_state.otp = str(
                secrets.randbelow(9000) + 1000
            )

            st.info(
                "Development OTP: "
                + st.session_state.otp
            )

        else:

            st.error(
                "Valid 10-digit mobile number required."
            )

    if st.session_state.otp:

        otp = st.text_input(
            "Enter OTP",
            max_chars=4
        )

        if st.button(
            "Verify & Continue"
        ):

            if otp == st.session_state.otp:

                st.session_state.user_mobile = mobile

                existing = q(
                    """
                    SELECT mobile
                    FROM users
                    WHERE mobile=?
                    LIMIT 1
                    """,
                    (mobile,)
                )

                if existing.empty:

                    start = date.today()

                    exec_sql(
                        """
                        INSERT INTO users(
                            mobile,
                            name,
                            reg_date,
                            trial_end_date,
                            is_paid,
                            role,
                            active
                        )
                        VALUES(?,?,?,?,?,?,?)
                        """,
                        (
                            mobile,
                            "Business User",
                            str(start),
                            str(
                                start
                                + timedelta(days=10)
                            ),
                            0,
                            "Owner",
                            1
                        )
                    )

                else:

                    # Existing old user record
                    # missing values safely repaired.

                    exec_sql(
                        """
                        UPDATE users
                        SET active=COALESCE(active,1),
                            role=COALESCE(role,'Owner'),
                            name=COALESCE(
                                NULLIF(name,''),
                                'Business User'
                            ),
                            reg_date=COALESCE(
                                reg_date,
                                ?
                            ),
                            trial_end_date=COALESCE(
                                trial_end_date,
                                ?
                            ),
                            is_paid=COALESCE(
                                is_paid,
                                0
                            )
                        WHERE mobile=?
                        """,
                        (
                            str(date.today()),
                            str(
                                date.today()
                                + timedelta(days=10)
                            ),
                            mobile
                        )
                    )

                exec_sql(
                    """
                    INSERT OR IGNORE INTO settings(
                        user_mobile,
                        financial_year,
                        invoice_prefix,
                        purchase_prefix,
                        default_gst,
                        company_state_code,
                        invoice_terms,
                        currency
                    )
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        mobile,
                        fy_for(today()),
                        "INV",
                        "PUR",
                        18,
                        "",
                        "",
                        "INR"
                    )
                )

                ensure_accounts()

                st.session_state.otp = None

                st.success(
                    "Login successful."
                )

                st.rerun()

            else:

                st.error(
                    "Invalid OTP."
                )

    st.stop()


# ============================================================
# USER CHECK
# ============================================================

user = user_row()

if not user:

    st.session_state.user_mobile = None
    st.session_state.otp = None

    st.error(
        "User session could not be loaded. "
        "Please login again."
    )

    st.rerun()


# ============================================================
# SETTINGS ENSURE
# ============================================================

if not settings_row():

    exec_sql(
        """
        INSERT OR IGNORE INTO settings(
            user_mobile,
            financial_year,
            invoice_prefix,
            purchase_prefix,
            default_gst,
            company_state_code,
            invoice_terms,
            currency
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            current_user(),
            fy_for(today()),
            "INV",
            "PUR",
            18,
            user.get("state_code") or "",
            "",
            "INR"
        )
    )


ensure_accounts()


# ============================================================
# BUSINESS PROFILE
# ============================================================

if not user.get("business_name"):

    st.markdown(
        """
        <div class="main-header">
            <h1>🏢 Business Setup</h1>
            <p>
                Complete your business details
                before launching the ERP.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("business_setup"):

        business_name = st.text_input(
            "Business Name"
        )

        address = st.text_area(
            "Business Address"
        )

        gstin = st.text_input(
            "GSTIN"
        )

        state_code = st.text_input(
            "State Code",
            max_chars=2
        )

        submitted = st.form_submit_button(
            "Save & Launch"
        )

        if submitted:

            if not business_name.strip():

                st.error(
                    "Business name is required."
                )

            else:

                exec_sql(
                    """
                    UPDATE users
                    SET business_name=?,
                        business_address=?,
                        gstin=?,
                        state_code=?
                    WHERE mobile=?
                    """,
                    (
                        business_name.strip(),
                        address.strip(),
                        gstin.strip().upper(),
                        state_code.strip(),
                        current_user()
                    )
                )

                exec_sql(
                    """
                    UPDATE settings
                    SET company_state_code=?
                    WHERE user_mobile=?
                    """,
                    (
                        state_code.strip(),
                        current_user()
                    )
                )

                st.success(
                    "Business setup completed."
                )

                st.rerun()

    st.stop()


# ============================================================
# SUBSCRIPTION CHECK
# ============================================================

expired = False

try:

    trial_date = user.get(
        "trial_end_date"
    )

    paid_date = user.get(
        "paid_till"
    )

    is_paid = int(
        user.get(
            "is_paid",
            0
        ) or 0
    )

    if not is_paid and trial_date:

        trial_expired = (
            date.today()
            >
            datetime.strptime(
                str(trial_date),
                "%Y-%m-%d"
            ).date()
        )

        expired = trial_expired

    elif is_paid and paid_date:

        paid_expired = (
            date.today()
            >
            datetime.strptime(
                str(paid_date),
                "%Y-%m-%d"
            ).date()
        )

        expired = paid_expired

except Exception:

    expired = False


if expired:

    st.error(
        "Your trial/subscription has expired."
    )

    st.stop()


# ============================================================
# PART 1 COMPLETE
# ============================================================
