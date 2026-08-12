import streamlit as st
import sqlite3
import io
import zipfile
import hashlib
import secrets
import json
import os
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
# PART 1
# ============================================================

APP_NAME = "SD TALLY BUSINESS"
APP_VERSION = "4.0.0"
DB_FILE = "sd_tally_business_enterprise.db"


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# GLOBAL STYLE
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
# DATABASE CONNECTION
# ============================================================

def db():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


def q(sql, params=()):
    con = db()

    try:
        if pd is None:
            raise RuntimeError(
                "pandas is required. Install using: pip install pandas"
            )

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
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    con = db()
    c = con.cursor()

    tables = [

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
        """,

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
        """,

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
        """,

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
        """,

        """
        CREATE TABLE IF NOT EXISTS godowns(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            godown_name TEXT,
            address TEXT,
            active INTEGER DEFAULT 1,
            UNIQUE(user_mobile, godown_name)
        )
        """,

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
        """,

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
        """,

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
        """,

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
        """,

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
        """,

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
        """,

        """
        CREATE TABLE IF NOT EXISTS allocations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            txn_id INTEGER,
            invoice_id INTEGER,
            amount REAL
        )
        """,

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
        """,

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
        """,

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
        """,

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
        """,

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
        """,

        """
        CREATE TABLE IF NOT EXISTS branding(
            user_mobile TEXT PRIMARY KEY,
            logo_b64 TEXT,
            signature_b64 TEXT,
            bank_details TEXT
        )
        """
    ]

    for table_sql in tables:
        c.execute(table_sql)

    con.commit()
    con.close()


init_db()


# ============================================================
# GENERAL HELPERS
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

    if not current_user():
        return None

    data = q(
        """
        SELECT *
        FROM users
        WHERE mobile=?
        AND active=1
        """,
        (current_user(),)
    )

    if data.empty:
        return None

    return data.iloc[0].to_dict()


def settings_row():

    if not current_user():
        return {}

    data = q(
        """
        SELECT *
        FROM settings
        WHERE user_mobile=?
        """,
        (current_user(),)
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

    if not current_user():
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
            current_user(),
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
# ACCOUNT MASTER
# ============================================================

def ensure_accounts():

    defaults = [

        (
            "Cash",
            "Cash",
            "Asset"
        ),

        (
            "Bank",
            "Bank",
            "Asset"
        ),

        (
            "Sales",
            "Sales",
            "Income"
        ),

        (
            "Purchase",
            "Purchase",
            "Expense"
        ),

        (
            "CGST Output",
            "GST",
            "Liability"
        ),

        (
            "SGST Output",
            "GST",
            "Liability"
        ),

        (
            "IGST Output",
            "GST",
            "Liability"
        ),

        (
            "CGST Input",
            "GST",
            "Asset"
        ),

        (
            "SGST Input",
            "GST",
            "Asset"
        ),

        (
            "IGST Input",
            "GST",
            "Asset"
        ),

        (
            "Capital",
            "Capital",
            "Equity"
        ),

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


def account_names():

    data = q(
        """
        SELECT name
        FROM accounts
        WHERE user_mobile=?
        AND active=1
        ORDER BY name
        """,
        (current_user(),)
    )

    if data.empty:
        return []

    return data["name"].tolist()


# ============================================================
# PARTY / ITEM HELPERS
# ============================================================

def party_options(party_type=None):

    if party_type:

        return q(
            """
            SELECT id, party_name
            FROM parties
            WHERE user_mobile=?
            AND party_type IN (?, 'Both')
            AND active=1
            ORDER BY party_name
            """,
            (
                current_user(),
                party_type
            )
        )

    return q(
        """
        SELECT id, party_name
        FROM parties
        WHERE user_mobile=?
        AND active=1
        ORDER BY party_name
        """,
        (current_user(),)
    )


def item_options():

    return q(
        """
        SELECT *
        FROM items
        WHERE user_mobile=?
        AND active=1
        ORDER BY item_name
        """,
        (current_user(),)
    )


# ============================================================
# VOUCHER NUMBER
# ============================================================

def next_no(kind):

    settings = settings_row()

    if kind == "Sales":
        prefix = settings.get(
            "invoice_prefix",
            "INV"
        )
    else:
        prefix = settings.get(
            "purchase_prefix",
            "PUR"
        )

    fy = fy_for(today())

    data = q(
        """
        SELECT voucher_no
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            current_user(),
            kind
        )
    )

    number = 1

    if not data.empty:

        value = str(
            data.iloc[0]["voucher_no"]
        )

        try:
            number = (
                int(
                    value.split("-")[-1]
                ) + 1
            )
        except Exception:
            number = 1

    return (
        f"{prefix}-{fy}-{number:05d}"
    )


# ============================================================
# GST CALCULATION
# ============================================================

def gst_split(
    taxable,
    gst_rate,
    same_state=True
):

    taxable = float(taxable or 0)
    gst_rate = float(gst_rate or 0)

    tax = round(
        taxable * gst_rate / 100,
        2
    )

    if same_state:
        half = round(
            tax / 2,
            2
        )

        return (
            half,
            round(tax - half, 2),
            0.0
        )

    return (
        0.0,
        0.0,
        tax
    )


# ============================================================
# STOCK BALANCE
# ============================================================

def stock_balance(
    item_id,
    godown=None
):

    params = [
        current_user(),
        item_id
    ]

    sql = """
        SELECT
            COALESCE(
                SUM(qty_in - qty_out),
                0
            ) AS qty
        FROM stock_moves
        WHERE user_mobile=?
        AND item_id=?
    """

    if godown:

        sql += """
            AND godown=?
        """

        params.append(godown)

    data = q(
        sql,
        tuple(params)
    )

    if data.empty:
        return 0.0

    return float(
        data.iloc[0]["qty"] or 0
    )


# ============================================================
# STOCK MOVEMENT
# ============================================================

def add_stock(
    voucher_id,
    vdate,
    item_id,
    item_name,
    godown,
    qty_in,
    qty_out,
    rate,
    move_type,
    batch="",
    expiry="",
    ref=""
):

    return exec_sql(
        """
        INSERT INTO stock_moves(
            user_mobile,
            vdate,
            voucher_id,
            item_id,
            item_name,
            godown,
            batch_no,
            expiry_date,
            move_type,
            qty_in,
            qty_out,
            rate,
            reference_no
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            current_user(),
            vdate,
            voucher_id,
            item_id,
            item_name,
            godown,
            batch,
            expiry,
            move_type,
            qty_in,
            qty_out,
            rate,
            ref
        )
    )


# ============================================================
# JOURNAL POSTING
# ============================================================

def post_journal(
    voucher_id,
    voucher_type,
    voucher_no,
    vdate,
    entries,
    narration=""
):

    """
    entries format:

    [
        ("Account", debit, credit),
        ("Account", debit, credit)
    ]
    """

    total_debit = 0.0
    total_credit = 0.0

    for account, debit, credit in entries:

        debit = float(debit or 0)
        credit = float(credit or 0)

        total_debit += debit
        total_credit += credit

        exec_sql(
            """
            INSERT INTO journal(
                user_mobile,
                voucher_id,
                vdate,
                voucher_type,
                voucher_no,
                account_name,
                debit,
                credit,
                narration
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                current_user(),
                voucher_id,
                vdate,
                voucher_type,
                voucher_no,
                account,
                debit,
                credit,
                narration
            )
        )

    # Accounting integrity check
    if round(total_debit, 2) != round(
        total_credit,
        2
    ):

        raise ValueError(
            "Journal is not balanced. "
            f"Debit={total_debit:.2f}, "
            f"Credit={total_credit:.2f}"
        )

    log(
        "POST",
        "journal",
        voucher_id,
        f"{voucher_type} {voucher_no}"
    )


# ============================================================
# PDF INVOICE
# ============================================================

def invoice_pdf(voucher_id):

    if not REPORTLAB_OK:
        return None

    header = q(
        """
        SELECT *
        FROM vouchers
        WHERE id=?
        AND user_mobile=?
        """,
        (
            voucher_id,
            current_user()
        )
    )

    if header.empty:
        return None

    items = q(
        """
        SELECT *
        FROM voucher_items
        WHERE voucher_id=?
        ORDER BY id
        """,
        (voucher_id,)
    )

    row = header.iloc[0]
    user = user_row()

    bio = io.BytesIO()

    doc = SimpleDocTemplate(
        bio,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            f"<b>{user.get('business_name','')}</b>",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            f"{user.get('business_address','')}"
            f"<br/>GSTIN: {user.get('gstin','')}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            f"<b>Tax Invoice</b> "
            f"#{row['voucher_no']} "
            f"| Date: {row['vdate']}",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"Party: {row['party_name']}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 10)
    )

    table_data = [
        [
            "Item",
            "HSN",
            "Qty",
            "Rate",
            "Disc",
            "Taxable",
            "GST",
            "Total"
        ]
    ]

    for _, item in items.iterrows():

        table_data.append(
            [
                item["item_name"],
                item["hsn_sac"],
                item["qty"],
                item["rate"],
                item["discount"],
                item["taxable"],
                (
                    item["cgst"]
                    + item["sgst"]
                    + item["igst"]
                ),
                item["total"]
            ]
        )

    table_data.extend(
        [
            [
                "",
                "",
                "",
                "",
                "",
                "Taxable",
                row["taxable"],
                ""
            ],
            [
                "",
                "",
                "",
                "",
                "",
                "CGST",
                row["cgst"],
                ""
            ],
            [
                "",
                "",
                "",
                "",
                "",
                "SGST",
                row["sgst"],
                ""
            ],
            [
                "",
                "",
                "",
                "",
                "",
                "IGST",
                row["igst"],
                ""
            ],
            [
                "",
                "",
                "",
                "",
                "",
                "Grand Total",
                row["total"],
                ""
            ]
        ]
    )

    table = Table(
        table_data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "RIGHT"
                )
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 12)
    )

    terms = settings_row().get(
        "invoice_terms",
        ""
    )

    if terms:
        story.append(
            Paragraph(
                terms,
                styles["Normal"]
            )
        )

    doc.build(story)

    return bio.getvalue()


# ============================================================
# SESSION STATE
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
# LOGIN SCREEN
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
                            role
                        )
                        VALUES(?,?,?,?,?)
                        """,
                        (
                            mobile,
                            "Business User",
                            str(start),
                            str(
                                start
                                + timedelta(days=10)
                            ),
                            "Owner"
                        )
                    )

                ensure_accounts()

                st.rerun()

            else:

                st.error(
                    "Invalid OTP."
                )

    st.stop()


# ============================================================
# USER VALIDATION
# ============================================================

user = user_row()

if not user:

    st.session_state.user_mobile = None
    st.rerun()


# ============================================================
# BUSINESS PROFILE SETUP
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
                    INSERT OR IGNORE INTO settings(
                        user_mobile,
                        financial_year,
                        company_state_code,
                        invoice_terms
                    )
                    VALUES(?,?,?,?)
                    """,
                    (
                        current_user(),
                        fy_for(today()),
                        state_code.strip(),
                        "Goods once sold are subject to business return policy."
                    )
                )

                ensure_accounts()

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

    trial_expired = (
        not user["is_paid"]
        and date.today()
        > datetime.strptime(
            user["trial_end_date"],
            "%Y-%m-%d"
        ).date()
    )

    paid_expired = (
        user["is_paid"]
        and user["paid_till"]
        and date.today()
        > datetime.strptime(
            user["paid_till"],
            "%Y-%m-%d"
        ).date()
    )

    expired = (
        trial_expired
        or paid_expired
    )

except Exception:

    expired = False


if expired:

    st.error(
        "Your trial/subscription has expired."
    )

    st.stop()


# ============================================================
# MAKE SURE DEFAULT ACCOUNTS EXIST
# ============================================================

ensure_accounts()


# ============================================================
# PART 1 END
# ============================================================
