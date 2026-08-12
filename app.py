import streamlit as st
import pandas as pd
import sqlite3
import random
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ============================================================
# SD TALLY BUSINESS - ENTERPRISE EDITION
# Stable Streamlit + SQLite Base
# ============================================================

st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "sd_tally_v32_permanent.db"


# ============================================================
# PROFESSIONAL CSS
# ============================================================

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"] {
    background: #f8fafc !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0;
}

[data-testid="stSidebar"] * {
    color: #0f172a !important;
}

.main-title {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    padding: 24px;
    border-radius: 14px;
    margin-bottom: 22px;
    box-shadow: 0 5px 18px rgba(0,0,0,.08);
}

.main-title h1 {
    color: #38bdf8 !important;
    margin: 0;
    font-size: 2rem;
}

.main-title p {
    color: #cbd5e1 !important;
    margin: 6px 0 0 0;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 3px 10px rgba(0,0,0,.05);
    margin-bottom: 15px;
}

.user-card {
    background: #f1f5f9;
    padding: 14px;
    border-radius: 10px;
    border-left: 4px solid #0284c7;
    margin-bottom: 12px;
}

.plan-card {
    background: #e0f2fe;
    color: #0369a1 !important;
    padding: 14px;
    border-radius: 10px;
    margin-bottom: 15px;
}

.stButton > button {
    width: 100%;
    min-height: 45px;
    border-radius: 9px;
    background: #0284c7;
    color: white !important;
    font-weight: 700;
    border: none;
}

.stButton > button:hover {
    background: #0369a1;
}

[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #e2e8f0 !important;
    border-left: 5px solid #0284c7 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.05);
}

.footer {
    text-align:center;
    color:#64748b;
    padding:25px;
    margin-top:40px;
}

@media(max-width:768px) {
    .main-title h1 {
        font-size: 1.45rem;
    }

    .main-title {
        padding: 18px;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE
# ============================================================

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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
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
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            item_name TEXT,
            unit TEXT DEFAULT 'PCS',
            barcode TEXT,
            hsn_sac TEXT,
            godown TEXT DEFAULT 'Main Store',
            batch_no TEXT,
            expiry_date TEXT,
            sale_price REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            stock_qty REAL DEFAULT 0,
            min_stock_alert REAL DEFAULT 5,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS godowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            godown_name TEXT,
            address TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            party_name TEXT,
            gstin TEXT,
            mobile TEXT,
            party_type TEXT,
            opening_balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            bank_name TEXT,
            account_no TEXT,
            ifsc_code TEXT,
            branch_name TEXT,
            opening_balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            date TEXT,
            party_name TEXT,
            item_name TEXT,
            unit TEXT DEFAULT 'PCS',
            hsn_sac TEXT,
            qty REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            taxable_amt REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            total_amt REAL DEFAULT 0,
            payment_mode TEXT,
            eway_bill_no TEXT,
            irn_no TEXT,
            debit_account TEXT,
            credit_account TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS capital_bank_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            date TEXT,
            account_type TEXT,
            particulars TEXT,
            amount REAL DEFAULT 0,
            txn_type TEXT,
            bank_name TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS branding (
            user_mobile TEXT PRIMARY KEY,
            logo_base64 TEXT,
            sig_base64 TEXT
        )
    """)

    # --------------------------------------------------------
    # SAFE MIGRATION FOR OLD DATABASE
    # --------------------------------------------------------

    migrations = [
        ("users", "business_address", "TEXT"),
        ("users", "gstin", "TEXT"),
        ("users", "trial_end_date", "TEXT"),
        ("users", "is_paid", "INTEGER DEFAULT 0"),
        ("users", "paid_till", "TEXT"),
        ("users", "role", "TEXT DEFAULT 'Owner'"),

        ("inventory", "barcode", "TEXT"),
        ("inventory", "hsn_sac", "TEXT"),
        ("inventory", "godown", "TEXT DEFAULT 'Main Store'"),
        ("inventory", "batch_no", "TEXT"),
        ("inventory", "expiry_date", "TEXT"),
        ("inventory", "sale_price", "REAL DEFAULT 0"),
        ("inventory", "purchase_price", "REAL DEFAULT 0"),
        ("inventory", "gst_rate", "REAL DEFAULT 0"),
        ("inventory", "stock_qty", "REAL DEFAULT 0"),
        ("inventory", "min_stock_alert", "REAL DEFAULT 5"),

        ("vouchers", "item_name", "TEXT"),
        ("vouchers", "unit", "TEXT DEFAULT 'PCS'"),
        ("vouchers", "hsn_sac", "TEXT"),
        ("vouchers", "qty", "REAL DEFAULT 0"),
        ("vouchers", "rate", "REAL DEFAULT 0"),
        ("vouchers", "taxable_amt", "REAL DEFAULT 0"),
        ("vouchers", "gst_rate", "REAL DEFAULT 0"),
        ("vouchers", "cgst", "REAL DEFAULT 0"),
        ("vouchers", "sgst", "REAL DEFAULT 0"),
        ("vouchers", "igst", "REAL DEFAULT 0"),
        ("vouchers", "total_amt", "REAL DEFAULT 0"),
        ("vouchers", "payment_mode", "TEXT"),
        ("vouchers", "eway_bill_no", "TEXT"),
        ("vouchers", "irn_no", "TEXT"),
        ("vouchers", "debit_account", "TEXT"),
        ("vouchers", "credit_account", "TEXT")
    ]

    for table, column, definition in migrations:
        add_column_if_missing(conn, table, column, definition)

    conn.commit()
    conn.close()


init_db()


# ============================================================
# SESSION
# ============================================================

defaults = {
    "user_mobile": None,
    "user_role": "Owner",
    "business_name": None,
    "business_gstin": "URP",
    "otp_sent": False,
    "generated_otp": None,
    "cart_items": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# URL SESSION RESTORE
# ============================================================

try:
    saved_mobile = st.query_params.get("user_session")

    if (
        not st.session_state.user_mobile
        and saved_mobile
        and str(saved_mobile).isdigit()
    ):
        st.session_state.user_mobile = str(saved_mobile)

except Exception:
    pass


# ============================================================
# USER / SUBSCRIPTION
# ============================================================

def get_user(mobile):

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE mobile=?
        """,
        (mobile,)
    ).fetchone()

    conn.close()

    return row


def get_subscription(mobile):

    user = get_user(mobile)

    if not user:
        return "NEW_USER"

    st.session_state.user_role = user["role"] or "Owner"
    st.session_state.business_name = user["business_name"]
    st.session_state.business_gstin = user["gstin"] or "URP"

    today = datetime.now().date()

    try:
        trial_end = datetime.strptime(
            user["trial_end_date"],
            "%Y-%m-%d"
        ).date()
    except Exception:
        trial_end = today

    if user["is_paid"] == 1 and user["paid_till"]:

        try:
            paid_till = datetime.strptime(
                user["paid_till"],
                "%Y-%m-%d"
            ).date()

            if today <= paid_till:
                return "ACTIVE PRO"

        except Exception:
            pass

    if today <= trial_end:

        days = (trial_end - today).days

        return f"FREE TRIAL • {days} DAYS LEFT"

    return "EXPIRED"


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.user_mobile:

    st.markdown("""
    <div class="main-title">
        <h1>🏢 SD TALLY BUSINESS</h1>
        <p>Professional Billing • Accounting • Inventory • GST • Reports</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.subheader("🔐 Secure Business Login")

        mobile = st.text_input(
            "📱 Mobile Number",
            max_chars=10,
            placeholder="Enter 10 digit mobile number"
        )

        if not st.session_state.otp_sent:

            if st.button("📨 Send Verification OTP"):

                if len(mobile) == 10 and mobile.isdigit():

                    otp = str(random.randint(1000, 9999))

                    st.session_state.generated_otp = otp
                    st.session_state.otp_sent = True

                    st.success("OTP generated successfully.")
                    st.info(
                        f"Testing OTP: {otp}"
                    )

                else:

                    st.error(
                        "Please enter a valid 10 digit mobile number."
                    )

        else:

            otp_input = st.text_input(
                "🔑 Enter 4 Digit OTP",
                max_chars=4
            )

            role = st.selectbox(
                "👤 Access Role",
                [
                    "Owner",
                    "Salesman / Staff"
                ]
            )

            if st.button("✅ Verify & Open Business"):

                if otp_input == st.session_state.generated_otp:

                    conn = get_db()

                    existing = conn.execute(
                        "SELECT mobile FROM users WHERE mobile=?",
                        (mobile,)
                    ).fetchone()

                    if not existing:

                        today = datetime.now().date()

                        trial_end = (
                            today + timedelta(days=10)
                        )

                        conn.execute(
                            """
                            INSERT INTO users
                            (
                                mobile,
                                name,
                                reg_date,
                                trial_end_date,
                                is_paid,
                                role
                            )
                            VALUES (?, ?, ?, ?, 0, ?)
                            """,
                            (
                                mobile,
                                "Business User",
                                str(today),
                                str(trial_end),
                                role
                            )
                        )

                    else:

                        conn.execute(
                            """
                            UPDATE users
                            SET role=?
                            WHERE mobile=?
                            """,
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

                    st.rerun()

                else:

                    st.error("❌ Invalid OTP.")

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    st.stop()


# ============================================================
# PROFILE SETUP
# ============================================================

subscription = get_subscription(
    st.session_state.user_mobile
)

if not st.session_state.business_name:

    st.markdown("""
    <div class="main-title">
        <h1>🏢 Business Profile Setup</h1>
        <p>Create your professional business workspace</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📋 Business Information")

    b_name = st.text_input(
        "🏢 Business / Shop Name"
    )

    b_address = st.text_area(
        "📍 Business Address"
    )

    b_gst = st.text_input(
        "🧾 GSTIN",
        placeholder="Optional"
    )

    if st.button("🚀 Save Profile & Launch"):

        if not b_name.strip():

            st.error("Business name is required.")

        else:

            conn = get_db()

            conn.execute(
                """
                UPDATE users
                SET business_name=?,
                    business_address=?,
                    gstin=?
                WHERE mobile=?
                """,
                (
                    b_name.strip(),
                    b_address.strip(),
                    b_gst.strip(),
                    st.session_state.user_mobile
                )
            )

            conn.commit()
            conn.close()

            st.session_state.business_name = b_name.strip()
            st.session_state.business_gstin = b_gst.strip()

            st.success("Business profile created.")

            st.rerun()

    st.stop()


# ============================================================
# SUBSCRIPTION
# ============================================================

if subscription == "EXPIRED":

    st.markdown("""
    <div class="main-title">
        <h1>💳 Subscription Renewal</h1>
        <p>Your free trial has expired.</p>
    </div>
    """, unsafe_allow_html=True)

    st.warning(
        "Renew your SD TALLY BUSINESS subscription to continue."
    )

    st.markdown(
        "### Renewal Amount: ₹112.10"
    )

    st.markdown(
        "### UPI ID: `8381085702@ibl`"
    )

    msg = urllib.parse.quote(
        "Hi, I have paid Rs.112.10 for SD Tally Business renewal. "
        f"Mobile: {st.session_state.user_mobile}"
    )

    st.markdown(
        f"""
        [📲 Send Payment Proof on WhatsApp]
        (https://wa.me/918381085702?text={msg})
        """
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    f"""
    <div class="user-card">
        👤 <b>Mobile</b><br>
        {st.session_state.user_mobile}<br><br>

        🏢 <b>Business</b><br>
        {st.session_state.business_name}<br><br>

        👨‍💼 <b>Role</b><br>
        {st.session_state.user_role}
    </div>

    <div class="plan-card">
        🎁 <b>Plan</b><br>
        {subscription}
    </div>
    """,
    unsafe_allow_html=True
)


if st.sidebar.button("🚪 Logout Account"):

    st.session_state.clear()

    try:
        st.query_params.clear()
    except Exception:
        pass

    st.rerun()


# ============================================================
# NAVIGATION
# ============================================================

MENU = [
    "🏠 Dashboard",
    "📁 Masters",
    "🛒 Purchase Entry",
    "📥 Purchase & GSTR-2B Import",
    "🧾 Tax Invoice (Sales)",
    "📦 Barcode Quick Billing",
    "🖨️ Thermal Receipt Print",
    "💰 All Tally Vouchers",
    "🏦 Capital & Bank Management",
    "📊 Bank Statement Import",
    "👥 Receivables & Party Statements",
    "🧮 GST Reports",
    "🚚 e-Way Bill & e-Invoice",
    "📈 Profit & Loss",
    "📋 Balance Sheet",
    "☁️ Automated Cloud Backup",
    "🏢 Branding & Signature",
    "💳 Account & Billing",
    "📦 Stock Summary & Ledger",
    "🔄 Sales / Purchase Return",
    "💸 Payment & Receipt",
    "📅 Day Book",
    "📒 Ledger & Trial Balance",
    "📑 Outstanding",
    "🔍 Voucher Search / Edit / Delete",
    "📊 Business Reports",
    "🔐 User & Permissions",
    "⚙️ Company Settings",
    "🖨️ Print & PDF",
    "📤 Excel / PDF Export"
]

st.sidebar.markdown("### 📌 Navigation")

menu = st.sidebar.selectbox(
    "Select Module",
    MENU
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="main-title">
        <h1>{st.session_state.business_name}</h1>
        <p>
            SD TALLY BUSINESS Enterprise |
            {st.session_state.user_mobile}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

user_mobile = st.session_state.user_mobile


# ============================================================
# DASHBOARD
# ============================================================

if menu in ["🏠 Dashboard", "📊 Business Reports"]:

    st.subheader("📊 Business Executive Dashboard")

    conn = get_db()

    sales = conn.execute(
        """
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type IN ('Sales','Tax Invoice')
        """,
        (user_mobile,)
    ).fetchone()[0]

    purchases = conn.execute(
        """
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        """,
        (user_mobile,)
    ).fetchone()[0]

    bank = conn.execute(
        """
        SELECT COALESCE(SUM(opening_balance),0)
        FROM bank_accounts
        WHERE user_mobile=?
        """,
        (user_mobile,)
    ).fetchone()[0]

    stock = conn.execute(
        """
        SELECT COALESCE(SUM(stock_qty),0)
        FROM inventory
        WHERE user_mobile=?
        """,
        (user_mobile,)
    ).fetchone()[0]

    conn.close()

    profit = sales - purchases

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Sales",
        f"₹ {sales:,.2f}"
    )

    c2.metric(
        "Purchases",
        f"₹ {purchases:,.2f}"
    )

    c3.metric(
        "Gross Profit",
        f"₹ {profit:,.2f}"
    )

    c4.metric(
        "Stock Qty",
        f"{stock:,.2f}"
    )

    st.divider()

    st.subheader("📈 Business Summary")

    chart = pd.DataFrame(
        {
            "Category": [
                "Sales",
                "Purchases",
                "Gross Profit"
            ],
            "Amount": [
                sales,
                purchases,
                profit
            ]
        }
    )

    st.bar_chart(
        chart.set_index("Category")
    )


# ============================================================
# MASTERS
# ============================================================

elif menu == "📁 Masters":

    st.subheader("📁 Masters Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "📦 Items",
            "🏢 Godowns",
            "👥 Parties"
        ]
    )

    # ---------------- ITEMS ----------------

    with tab1:

        item_name = st.text_input(
            "Item Name"
        )

        unit = st.selectbox(
            "Unit",
            [
                "PCS",
                "KG",
                "LTR",
                "MTR",
                "BOX",
                "BAG",
                "PACK"
            ]
        )

        sale_price = st.number_input(
            "Sale Price",
            min_value=0.0
        )

        purchase_price = st.number_input(
            "Purchase Price",
            min_value=0.0
        )

        gst_rate = st.selectbox(
            "GST %",
            [0.0, 5.0, 12.0, 18.0, 28.0]
        )

        opening_stock = st.number_input(
            "Opening Stock",
            min_value=0.0
        )

        if st.button(
            "💾 Save Item"
        ):

            if not item_name.strip():

                st.error(
                    "Item name is required."
                )

            else:

                conn = get_db()

                conn.execute(
                    """
                    INSERT INTO inventory
                    (
                        user_mobile,
                        item_name,
                        unit,
                        sale_price,
                        purchase_price,
                        gst_rate,
                        stock_qty
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_mobile,
                        item_name.strip(),
                        unit,
                        sale_price,
                        purchase_price,
                        gst_rate,
                        opening_stock
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "Item saved successfully."
                )

    # ---------------- GODOWN ----------------

    with tab2:

        godown_name = st.text_input(
            "Godown Name"
        )

        godown_address = st.text_area(
            "Godown Address"
        )

        if st.button(
            "💾 Save Godown"
        ):

            if not godown_name.strip():

                st.error(
                    "Godown name is required."
                )

            else:

                conn = get_db()

                conn.execute(
                    """
                    INSERT INTO godowns
                    (
                        user_mobile,
                        godown_name,
                        address
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        user_mobile,
                        godown_name.strip(),
                        godown_address.strip()
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "Godown saved successfully."
                )

    # ---------------- PARTY ----------------

    with tab3:

        party_name = st.text_input(
            "Party Name"
        )

        party_type = st.selectbox(
            "Party Type",
            [
                "Customer",
                "Supplier"
            ]
        )

        party_mobile = st.text_input(
            "Party Mobile"
        )

        party_gstin = st.text_input(
            "Party GSTIN"
        )

        opening_balance = st.number_input(
            "Opening Balance",
            min_value=0.0
        )

        if st.button(
            "💾 Save Party"
        ):

            if not party_name.strip():

                st.error(
                    "Party name is required."
                )

            else:

                conn = get_db()

                conn.execute(
                    """
                    INSERT INTO parties
                    (
                        user_mobile,
                        party_name,
                        gstin,
                        mobile,
                        party_type,
                        opening_balance
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_mobile,
                        party_name.strip(),
                        party_gstin.strip(),
                        party_mobile.strip(),
                        party_type,
                        opening_balance
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "Party created successfully."
                )


# ============================================================
# SALES INVOICE
# ============================================================

elif menu == "🧾 Tax Invoice (Sales)":

    st.subheader(
        "🧾 Tax Invoice / Sales"
    )

    conn = get_db()

    customers = conn.execute(
        """
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND party_type='Customer'
        ORDER BY party_name
        """,
        (user_mobile,)
    ).fetchall()

    items = conn.execute(
        """
        SELECT item_name, unit, sale_price, gst_rate
        FROM inventory
        WHERE user_mobile=?
        ORDER BY item_name
        """,
        (user_mobile,)
    ).fetchall()

    conn.close()

    invoice_no = st.text_input(
        "Invoice Number",
        value=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    if customers:

        customer_names = [
            r["party_name"]
            for r in customers
        ]

        customer = st.selectbox(
            "Customer",
            customer_names
        )

    else:

        customer = st.text_input(
            "Customer Name"
        )

    if items:

        item_names = [
            r["item_name"]
            for r in items
        ]

        selected_item = st.selectbox(
            "Item",
            item_names
        )

        selected = next(
            r for r in items
            if r["item_name"] == selected_item
        )

        rate = float(selected["sale_price"])
        gst = float(selected["gst_rate"])
        unit = selected["unit"]

    else:

        selected_item = st.text_input(
            "Item Name"
        )

        unit = st.selectbox(
            "Unit",
            ["PCS", "KG", "LTR", "BOX"]
        )

        rate = st.number_input(
            "Rate",
            min_value=0.0
        )

        gst = st.number_input(
            "GST %",
            min_value=0.0,
            max_value=28.0,
            value=18.0
        )

    qty = st.number_input(
        "Quantity",
        min_value=0.01,
        value=1.0
    )

    payment_mode = st.selectbox(
        "Payment Mode",
        [
            "Cash",
            "Bank / UPI",
            "Credit (Pending)"
        ]
    )

    taxable = qty * rate
    gst_amount = taxable * gst / 100
    total = taxable + gst_amount

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Taxable",
        f"₹ {taxable:,.2f}"
    )

    c2.metric(
        "GST",
        f"₹ {gst_amount:,.2f}"
    )

    c3.metric(
        "Grand Total",
        f"₹ {total:,.2f}"
    )

    if st.button(
        "💾 Save Tax Invoice"
    ):

        conn = get_db()

        conn.execute(
            """
            INSERT INTO vouchers
            (
                user_mobile,
                voucher_type,
                voucher_no,
                date,
                party_name,
                item_name,
                unit,
                qty,
                rate,
                taxable_amt,
                gst_rate,
                cgst,
                sgst,
                total_amt,
                payment_mode
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_mobile,
                "Tax Invoice",
                invoice_no,
                str(datetime.now().date()),
                customer,
                selected_item,
                unit,
                qty,
                rate,
                taxable,
                gst,
                gst_amount / 2,
                gst_amount / 2,
                total,
                payment_mode
            )
        )

        # Reduce stock
        conn.execute(
            """
            UPDATE inventory
            SET stock_qty = stock_qty - ?
            WHERE user_mobile=?
            AND item_name=?
            """,
            (
                qty,
                user_mobile,
                selected_item
            )
        )

        conn.commit()
        conn.close()

        st.success(
            f"Invoice {invoice_no} saved successfully."
        )


# ============================================================
# PURCHASE
# ============================================================

elif menu == "🛒 Purchase Entry":

    st.subheader(
        "🛒 Purchase Entry"
    )

    conn = get_db()

    suppliers = conn.execute(
        """
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND party_type='Supplier'
        ORDER BY party_name
        """,
        (user_mobile,)
    ).fetchall()

    conn.close()

    supplier = (
        st.selectbox(
            "Supplier",
            [r["party_name"] for r in suppliers]
        )
        if suppliers
        else st.text_input("Supplier Name")
    )

    item = st.text_input(
        "Item Name"
    )

    qty = st.number_input(
        "Quantity",
        min_value=0.01
    )

    rate = st.number_input(
        "Purchase Rate",
        min_value=0.0
    )

    gst = st.number_input(
        "GST %",
        min_value=0.0,
        max_value=28.0,
        value=18.0
    )

    taxable = qty * rate
    gst_amount = taxable * gst / 100
    total = taxable + gst_amount

    st.metric(
        "Purchase Total",
        f"₹ {total:,.2f}"
    )

    if st.button(
        "💾 Save Purchase"
    ):

        conn = get_db()

        conn.execute(
            """
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
            VALUES
            (?, 'Purchase', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_mobile,
                f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                str(datetime.now().date()),
                supplier,
                item,
                qty,
                rate,
                taxable,
                gst,
                gst_amount / 2,
                gst_amount / 2,
                total,
                "Credit"
            )
        )

        # Add stock
        existing = conn.execute(
            """
            SELECT id
            FROM inventory
            WHERE user_mobile=?
            AND item_name=?
            """,
            (user_mobile, item)
        ).fetchone()

        if existing:

            conn.execute(
                """
                UPDATE inventory
                SET stock_qty=stock_qty+?,
                    purchase_price=?,
                    gst_rate=?
                WHERE id=?
                """,
                (
                    qty,
                    rate,
                    gst,
                    existing["id"]
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO inventory
                (
                    user_mobile,
                    item_name,
                    unit,
                    purchase_price,
                    gst_rate,
                    stock_qty
                )
                VALUES (?, ?, 'PCS', ?, ?, ?)
                """,
                (
                    user_mobile,
                    item,
                    rate,
                    gst,
                    qty
                )
            )

        conn.commit()
        conn.close()

        st.success(
            "Purchase saved and stock updated."
        )


# ============================================================
# STOCK
# ============================================================

elif menu == "📦 Stock Summary & Ledger":

    st.subheader(
        "📦 Stock Summary & Stock Ledger"
    )

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT
            item_name AS Item,
            unit AS Unit,
            sale_price AS Sale_Price,
            purchase_price AS Purchase_Price,
            gst_rate AS GST,
            stock_qty AS Stock
        FROM inventory
        WHERE user_mobile=?
        ORDER BY item_name
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    if df.empty:
        st.info(
            "No stock items available."
        )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# DAY BOOK
# ============================================================

elif menu == "📅 Day Book":

    st.subheader(
        "📅 Day Book"
    )

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT
            date AS Date,
            voucher_type AS Voucher,
            voucher_no AS Number,
            party_name AS Party,
            total_amt AS Amount,
            payment_mode AS Payment
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY date DESC, id DESC
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# VOUCHER SEARCH / DELETE
# ============================================================

elif menu == "🔍 Voucher Search / Edit / Delete":

    st.subheader(
        "🔍 Voucher Register"
    )

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT
            id,
            voucher_type,
            voucher_no,
            date,
            party_name,
            total_amt,
            payment_mode
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY id DESC
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:

        voucher_id = st.selectbox(
            "Select Voucher ID",
            df["id"].tolist()
        )

        if st.button(
            "🗑️ Delete Voucher"
        ):

            conn = get_db()

            conn.execute(
                """
                DELETE FROM vouchers
                WHERE id=?
                AND user_mobile=?
                """,
                (
                    voucher_id,
                    user_mobile
                )
            )

            conn.commit()
            conn.close()

            st.success(
                "Voucher deleted successfully."
            )

            st.rerun()


# ============================================================
# PARTY / OUTSTANDING
# ============================================================

elif menu in [
    "👥 Receivables & Party Statements",
    "📑 Outstanding"
]:

    st.subheader(
        "👥 Receivables & Payables"
    )

    conn = get_db()

    customer_df = pd.read_sql_query(
        """
        SELECT
            party_name AS Customer,
            SUM(total_amt) AS Outstanding
        FROM vouchers
        WHERE user_mobile=?
        AND payment_mode='Credit (Pending)'
        GROUP BY party_name
        """,
        conn,
        params=(user_mobile,)
    )

    supplier_df = pd.read_sql_query(
        """
        SELECT
            party_name AS Supplier,
            SUM(total_amt) AS Payable
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND payment_mode='Credit'
        GROUP BY party_name
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("### Customer Outstanding")

        st.dataframe(
            customer_df,
            use_container_width=True,
            hide_index=True
        )

    with c2:

        st.markdown("### Supplier Payable")

        st.dataframe(
            supplier_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# LEDGER / TRIAL BALANCE
# ============================================================

elif menu == "📒 Ledger & Trial Balance":

    st.subheader(
        "📒 Ledger & Trial Balance"
    )

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT
            voucher_type AS Voucher,
            party_name AS Party,
            SUM(total_amt) AS Total
        FROM vouchers
        WHERE user_mobile=?
        GROUP BY voucher_type, party_name
        ORDER BY voucher_type
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PROFIT & LOSS
# ============================================================

elif menu == "📈 Profit & Loss":

    st.subheader(
        "📈 Profit & Loss Account"
    )

    conn = get_db()

    sales = conn.execute(
        """
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Tax Invoice'
        """,
        (user_mobile,)
    ).fetchone()[0]

    purchases = conn.execute(
        """
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        """,
        (user_mobile,)
    ).fetchone()[0]

    conn.close()

    profit = sales - purchases

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Sales",
        f"₹ {sales:,.2f}"
    )

    c2.metric(
        "Purchases",
        f"₹ {purchases:,.2f}"
    )

    c3.metric(
        "Gross Profit",
        f"₹ {profit:,.2f}"
    )


# ============================================================
# BANK
# ============================================================

elif menu == "🏦 Capital & Bank Management":

    st.subheader(
        "🏦 Bank Account Management"
    )

    bank_name = st.text_input(
        "Bank Name"
    )

    account_no = st.text_input(
        "Account Number"
    )

    ifsc = st.text_input(
        "IFSC Code"
    )

    branch = st.text_input(
        "Branch"
    )

    opening = st.number_input(
        "Opening Balance",
        min_value=0.0
    )

    if st.button(
        "💾 Save Bank Account"
    ):

        if not bank_name.strip():

            st.error(
                "Bank name is required."
            )

        else:

            conn = get_db()

            conn.execute(
                """
                INSERT INTO bank_accounts
                (
                    user_mobile,
                    bank_name,
                    account_no,
                    ifsc_code,
                    branch_name,
                    opening_balance
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_mobile,
                    bank_name,
                    account_no,
                    ifsc,
                    branch,
                    opening
                )
            )

            conn.commit()
            conn.close()

            st.success(
                "Bank account saved."
            )


# ============================================================
# THERMAL PRINT
# ============================================================

elif menu == "🖨️ Thermal Receipt Print":

    st.subheader(
        "🖨️ 58mm Thermal Receipt"
    )

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT
            voucher_no,
            date,
            party_name,
            total_amt
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY id DESC
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    if df.empty:

        st.info(
            "No invoices available for printing."
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
            margin:auto;
            padding:15px;
            background:white;
            color:black;
            font-family:monospace;
            border:1px dashed black;
        ">
            <center>
                <h3>{st.session_state.business_name}</h3>
                <div>GSTIN: {st.session_state.business_gstin}</div>
                <hr>
            </center>

            Invoice: {row['voucher_no']}<br>
            Date: {row['date']}<br>
            Customer: {row['party_name']}<br>

            <hr>

            <h3>Total: ₹ {float(row['total_amt']):,.2f}</h3>

            <center>
                <hr>
                Thank You!
            </center>
        </div>
        """

        components.html(
            receipt,
            height=380
        )


# ============================================================
# EXPORT / BACKUP
# ============================================================

elif menu in [
    "☁️ Automated Cloud Backup",
    "🖨️ Print & PDF",
    "📤 Excel / PDF Export"
]:

    st.subheader(
        "☁️ Backup & Report Export"
    )

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY id DESC
        """,
        conn,
        params=(user_mobile,)
    )

    conn.close()

    csv_data = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Download Voucher Backup",
        data=csv_data,
        file_name=(
            f"{st.session_state.business_name}_"
            f"Voucher_Backup.csv"
        ),
        mime="text/csv"
    )

    if not df.empty:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# OTHER MODULES
# ============================================================

else:

    st.subheader(
        menu
    )

    st.info(
        "This module is connected to your SD TALLY BUSINESS "
        "workspace and is ready for implementation."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        <b>SD TALLY BUSINESS</b><br>
        Professional Billing • Accounting • Inventory • GST<br>
        © 2026 SD TALLY BUSINESS
    </div>
    """,
    unsafe_allow_html=True
)
