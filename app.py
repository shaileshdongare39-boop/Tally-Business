import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ============================================================
# SD TALLY BUSINESS
# PART 1 — FOUNDATION + DATABASE + LOGIN
# ============================================================

st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE
# ============================================================

DB_FILE = "sd_tally_business.db"


def get_db():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            role TEXT DEFAULT 'Owner',
            business_name TEXT DEFAULT '',
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            pan TEXT DEFAULT '',
            state TEXT DEFAULT 'Maharashtra',
            state_code TEXT DEFAULT '27',
            financial_year TEXT DEFAULT '',
            trial_end TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            item_name TEXT,
            item_code TEXT DEFAULT '',
            unit TEXT DEFAULT 'PCS',
            hsn_sac TEXT DEFAULT '',
            gst_rate REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            opening_stock REAL DEFAULT 0,
            current_stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 5,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            party_name TEXT,
            party_type TEXT,
            mobile TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            state TEXT DEFAULT 'Maharashtra',
            opening_balance REAL DEFAULT 0,
            credit_limit REAL DEFAULT 0,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            date TEXT,
            party_name TEXT DEFAULT '',
            item_name TEXT DEFAULT '',
            qty REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            taxable_amount REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT '',
            narration TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            date TEXT,
            account_name TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            narration TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ============================================================
# HELPERS
# ============================================================

def today():
    return datetime.now().strftime("%Y-%m-%d")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    return f"₹ {float(value):,.2f}"


def get_user():

    mobile = st.session_state.get("user_mobile")

    if not mobile:
        return None

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE mobile=?",
        (mobile,)
    ).fetchone()

    conn.close()

    return row


def create_user(mobile, role):

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE mobile=?",
        (mobile,)
    ).fetchone()

    if not existing:

        d = datetime.now().date()
        trial_end = d + timedelta(days=10)

        conn.execute("""
            INSERT INTO users
            (
                mobile,
                name,
                role,
                trial_end,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            mobile,
            "Business User",
            role,
            str(trial_end),
            now()
        ))

        conn.commit()

    conn.close()


# ============================================================
# SESSION
# ============================================================

if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None

if "otp" not in st.session_state:
    st.session_state.otp = None

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.user_mobile:

    st.title("💼 SD TALLY BUSINESS")

    st.write(
        "Professional Billing • Accounting • Inventory • GST"
    )

    st.subheader("🔐 Mobile Login")

    mobile = st.text_input(
        "📱 10 Digit Mobile Number",
        max_chars=10
    )

    role = st.selectbox(
        "👤 Role",
        [
            "Owner",
            "Salesman / Staff"
        ]
    )

    if not st.session_state.otp_sent:

        if st.button("📨 SEND OTP"):

            if len(mobile) == 10 and mobile.isdigit():

                st.session_state.otp = "1234"
                st.session_state.otp_sent = True

                st.success(
                    "OTP sent successfully."
                )

                st.info(
                    "TEST OTP: 1234"
                )

            else:

                st.error(
                    "Please enter valid 10 digit mobile number."
                )

    else:

        otp = st.text_input(
            "🔑 Enter OTP",
            max_chars=4
        )

        if st.button("✅ VERIFY & LOGIN"):

            if otp == st.session_state.otp:

                create_user(
                    mobile,
                    role
                )

                st.session_state.user_mobile = mobile
                st.session_state.otp = None
                st.session_state.otp_sent = False

                st.rerun()

            else:

                st.error(
                    "❌ Invalid OTP"
                )

    st.stop()


# ============================================================
# USER
# ============================================================

user = get_user()

if user is None:

    st.session_state.user_mobile = None
    st.rerun()


# ============================================================
# BUSINESS SETUP
# ============================================================

business_name = user[4]

if not business_name:

    st.title("🏢 Business Setup")

    st.write(
        "Create your business profile."
    )

    with st.form("business_setup"):

        name = st.text_input(
            "🏢 Business Name *"
        )

        address = st.text_area(
            "📍 Address"
        )

        phone = st.text_input(
            "📱 Business Phone"
        )

        email = st.text_input(
            "📧 Email"
        )

        gstin = st.text_input(
            "🧾 GSTIN"
        )

        pan = st.text_input(
            "PAN"
        )

        state = st.text_input(
            "State",
            value="Maharashtra"
        )

        save = st.form_submit_button(
            "💾 SAVE BUSINESS"
        )

        if save:

            if not name.strip():

                st.error(
                    "Business name is required."
                )

            else:

                conn = get_db()

                conn.execute("""
                    UPDATE users
                    SET
                        business_name=?,
                        address=?,
                        phone=?,
                        email=?,
                        gstin=?,
                        pan=?,
                        state=?
                    WHERE mobile=?
                """, (
                    name,
                    address,
                    phone,
                    email,
                    gstin,
                    pan,
                    state,
                    st.session_state.user_mobile
                ))

                conn.commit()
                conn.close()

                st.success(
                    "✅ Business saved successfully."
                )

                st.rerun()

    st.stop()


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    f"💼 {business_name}"
)

st.caption(
    "SD TALLY BUSINESS • Professional Accounting System"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📂 MAIN MENU")

menu = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Dashboard",
        "⚙️ Masters",
        "🧾 Vouchers",
        "📊 Reports",
        "⚙️ Settings"
    ]
)

if st.sidebar.button("🚪 LOGOUT"):

    st.session_state.user_mobile = None
    st.session_state.otp = None
    st.session_state.otp_sent = False

    st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.header("🏠 Dashboard")

    conn = get_db()

    mob = st.session_state.user_mobile

    sales = conn.execute("""
        SELECT COALESCE(SUM(total_amount),0)
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
    """, (mob,)).fetchone()[0]

    purchase = conn.execute("""
        SELECT COALESCE(SUM(total_amount),0)
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
    """, (mob,)).fetchone()[0]

    stock = conn.execute("""
        SELECT COALESCE(
            SUM(current_stock * purchase_price),
            0
        )
        FROM items
        WHERE user_mobile=?
    """, (mob,)).fetchone()[0]

    items = conn.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE user_mobile=?
    """, (mob,)).fetchone()[0]

    parties = conn.execute("""
        SELECT COUNT(*)
        FROM parties
        WHERE user_mobile=?
    """, (mob,)).fetchone()[0]

    conn.close()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "💰 Sales",
        money(sales)
    )

    c2.metric(
        "🛒 Purchase",
        money(purchase)
    )

    c3.metric(
        "📦 Stock Value",
        money(stock)
    )

    c4.metric(
        "📈 Difference",
        money(sales - purchase)
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "📦 Items",
        items
    )

    c2.metric(
        "👥 Parties",
        parties
    )

    st.success(
        "✅ SD TALLY BUSINESS is ready."
    )


# ============================================================
# END PART 1
# ============================================================
