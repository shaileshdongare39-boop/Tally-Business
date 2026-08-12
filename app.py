import streamlit as st
import sqlite3
import pandas as pd
import random
import json
import base64
import io
from datetime import datetime, timedelta

# ============================================================
# SD TALLY BUSINESS ENTERPRISE
# STEP 1 — MASTER FOUNDATION
# ============================================================

st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROFESSIONAL UI
# ============================================================

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background:#f8fafc;
    color:#0f172a;
}

[data-testid="stSidebar"] {
    background:#ffffff;
    border-right:1px solid #e2e8f0;
}

.main-header {
    background:linear-gradient(135deg,#0f172a,#1e293b);
    padding:24px;
    border-radius:14px;
    margin-bottom:20px;
    color:white;
}

.main-header h1 {
    margin:0;
    color:#38bdf8 !important;
    font-size:2rem;
}

.main-header p {
    margin:5px 0 0 0;
    color:#cbd5e1;
}

.card {
    background:white;
    padding:18px;
    border-radius:12px;
    border:1px solid #e2e8f0;
    box-shadow:0 2px 5px rgba(0,0,0,.06);
    margin-bottom:15px;
}

.stButton>button {
    width:100%;
    min-height:45px;
    border-radius:8px;
    font-weight:700;
}

[data-testid="stMetric"] {
    background:white;
    border:1px solid #e2e8f0;
    border-radius:10px;
    padding:15px;
}

@media(max-width:768px) {
    .main-header h1 {
        font-size:1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATABASE
# ============================================================

DB_FILE = "sd_tally_business_enterprise.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():

    conn = get_db()
    c = conn.cursor()

    # ---------------- USERS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE NOT NULL,
        name TEXT,
        role TEXT DEFAULT 'Owner',
        business_name TEXT,
        business_address TEXT,
        business_phone TEXT,
        email TEXT,
        gstin TEXT,
        pan TEXT,
        state TEXT DEFAULT 'Maharashtra',
        state_code TEXT DEFAULT '27',
        financial_year TEXT,
        reg_date TEXT,
        trial_end_date TEXT,
        is_paid INTEGER DEFAULT 0,
        paid_till TEXT,
        created_at TEXT
    )
    """)

    # ---------------- ITEMS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        item_name TEXT,
        item_code TEXT,
        barcode TEXT,
        category TEXT,
        unit TEXT DEFAULT 'PCS',
        hsn_sac TEXT,
        gst_rate REAL DEFAULT 0,
        purchase_price REAL DEFAULT 0,
        sale_price REAL DEFAULT 0,
        opening_stock REAL DEFAULT 0,
        current_stock REAL DEFAULT 0,
        min_stock REAL DEFAULT 5,
        batch_no TEXT,
        expiry_date TEXT,
        godown TEXT DEFAULT 'Main Store',
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    # ---------------- PARTIES ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        party_name TEXT,
        party_type TEXT,
        mobile TEXT,
        email TEXT,
        address TEXT,
        gstin TEXT,
        state TEXT,
        state_code TEXT,
        opening_balance REAL DEFAULT 0,
        credit_limit REAL DEFAULT 0,
        credit_days INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    # ---------------- GODOWNS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS godowns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        godown_name TEXT,
        address TEXT,
        manager_name TEXT,
        mobile TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    # ---------------- BANKS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        bank_name TEXT,
        account_name TEXT,
        account_no TEXT,
        ifsc TEXT,
        branch TEXT,
        opening_balance REAL DEFAULT 0,
        current_balance REAL DEFAULT 0,
        upi_id TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    # ---------------- TRANSACTIONS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        voucher_type TEXT,
        voucher_no TEXT,
        date TEXT,
        party_name TEXT,
        item_name TEXT,
        unit TEXT,
        hsn_sac TEXT,
        qty REAL DEFAULT 0,
        rate REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        taxable_amount REAL DEFAULT 0,
        gst_rate REAL DEFAULT 0,
        cgst REAL DEFAULT 0,
        sgst REAL DEFAULT 0,
        igst REAL DEFAULT 0,
        round_off REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        payment_mode TEXT,
        debit_account TEXT,
        credit_account TEXT,
        narration TEXT,
        eway_bill_no TEXT,
        irn_no TEXT,
        created_at TEXT
    )
    """)

    # ---------------- LEDGER ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        date TEXT,
        account_name TEXT,
        account_type TEXT,
        voucher_type TEXT,
        voucher_no TEXT,
        particulars TEXT,
        debit REAL DEFAULT 0,
        credit REAL DEFAULT 0,
        balance REAL DEFAULT 0,
        created_at TEXT
    )
    """)

    # ---------------- STOCK MOVEMENT ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        date TEXT,
        item_name TEXT,
        godown TEXT,
        movement_type TEXT,
        reference_no TEXT,
        qty_in REAL DEFAULT 0,
        qty_out REAL DEFAULT 0,
        balance_qty REAL DEFAULT 0,
        rate REAL DEFAULT 0,
        created_at TEXT
    )
    """)

    # ---------------- CAPITAL ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS capital (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        date TEXT,
        entry_type TEXT,
        amount REAL,
        narration TEXT,
        created_at TEXT
    )
    """)

    # ---------------- EXPENSES ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        date TEXT,
        category TEXT,
        description TEXT,
        amount REAL,
        payment_mode TEXT,
        created_at TEXT
    )
    """)

    # ---------------- COMPANY BRANDING ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS branding (
        user_mobile TEXT PRIMARY KEY,
        logo TEXT,
        signature TEXT,
        stamp TEXT,
        invoice_template TEXT DEFAULT 'Professional'
    )
    """)

    # ---------------- AUDIT LOG ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        action TEXT,
        module TEXT,
        reference_no TEXT,
        timestamp TEXT
    )
    """)

    # ---------------- BACKUP RECORDS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        backup_name TEXT,
        created_at TEXT
    )
    """)

    # ---------------- SUBSCRIPTIONS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        plan_name TEXT,
        start_date TEXT,
        end_date TEXT,
        amount REAL DEFAULT 0,
        status TEXT DEFAULT 'TRIAL',
        payment_reference TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "user_mobile": None,
    "user_role": "Owner",
    "otp_sent": False,
    "otp": None,
    "business_name": None,
    "business_gstin": None,
    "cart": [],
    "page": "Dashboard"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def today():
    return datetime.now().strftime("%Y-%m-%d")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    try:
        return f"₹ {float(value):,.2f}"
    except:
        return "₹ 0.00"


def log_action(action, module="", reference=""):

    conn = get_db()
    conn.execute("""
        INSERT INTO audit_log
        (user_mobile, action, module, reference_no, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        st.session_state.user_mobile,
        action,
        module,
        reference,
        now()
    ))

    conn.commit()
    conn.close()


def get_user():

    if not st.session_state.user_mobile:
        return None

    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE mobile=?
    """, (st.session_state.user_mobile,)).fetchone()

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
                reg_date,
                trial_end_date,
                financial_year,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            mobile,
            "Business User",
            role,
            str(d),
            str(trial_end),
            f"{d.year}-{str(d.year+1)[-2:]}",
            now()
        ))

        conn.commit()

    conn.close()


def subscription_status():

    user = get_user()

    if not user:
        return "NEW"

    trial_end = user[14]
    paid = user[15]
    paid_till = user[16]

    today_date = datetime.now().date()

    if paid == 1 and paid_till:

        try:
            if today_date <= datetime.strptime(
                paid_till, "%Y-%m-%d"
            ).date():
                return "ACTIVE PRO"
        except:
            pass

    if trial_end:

        try:
            end = datetime.strptime(
                trial_end, "%Y-%m-%d"
            ).date()

            if today_date <= end:

                days = (end - today_date).days

                return f"FREE TRIAL - {days} DAYS LEFT"

        except:
            pass

    return "EXPIRED"


def units():

    return [
        "PCS",
        "NOS",
        "KG",
        "GM",
        "TON",
        "LTR",
        "ML",
        "MTR",
        "CM",
        "MM",
        "KM",
        "BOX",
        "PACK",
        "BAG",
        "BOTTLE",
        "DOZEN",
        "SET",
        "PAIR",
        "SQFT",
        "SQM",
        "CUSTOM"
    ]


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.user_mobile:

    st.markdown("""
    <div class="main-header">
        <h1>💼 SD TALLY BUSINESS</h1>
        <p>Professional Billing • Accounting • Inventory • GST</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🔐 Mobile Login")

    mobile = st.text_input(
        "📱 Enter 10 Digit Mobile Number",
        max_chars=10
    )

    role = st.selectbox(
        "👤 Access Role",
        ["Owner", "Salesman / Staff"]
    )

    if not st.session_state.otp_sent:

        if st.button("📨 SEND OTP"):

            if len(mobile) == 10 and mobile.isdigit():

                st.session_state.otp = str(
                    random.randint(1000, 9999)
                )

                st.session_state.otp_sent = True

                st.success("OTP generated for testing.")
                st.info(
                    f"🔑 TEST OTP: {st.session_state.otp}"
                )

            else:

                st.error(
                    "Please enter valid 10 digit mobile number."
                )

    else:

        otp_input = st.text_input(
            "🔑 Enter OTP",
            max_chars=4
        )

        if st.button("✅ VERIFY & LOGIN"):

            if otp_input == st.session_state.otp:

                create_user(mobile, role)

                st.session_state.user_mobile = mobile
                st.session_state.user_role = role

                st.session_state.otp_sent = False
                st.session_state.otp = None

                st.rerun()

            else:

                st.error("❌ Invalid OTP")

    st.stop()


# ============================================================
# USER PROFILE
# ============================================================

user = get_user()

if user:

    st.session_state.user_role = user[3]

    st.session_state.business_name = user[5]
    st.session_state.business_gstin = user[9]


# ============================================================
# BUSINESS ONBOARDING
# ============================================================

if not st.session_state.business_name:

    st.markdown("""
    <div class="main-header">
        <h1>🏢 Business Setup</h1>
        <p>Create your professional accounting workspace</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("business_setup"):

        business_name = st.text_input(
            "🏢 Business / Shop Name *"
        )

        address = st.text_area(
            "📍 Business Address"
        )

        phone = st.text_input(
            "📱 Business Phone"
        )

        email = st.text_input(
            "📧 Business Email"
        )

        gstin = st.text_input(
            "🧾 GSTIN (Optional)"
        )

        pan = st.text_input(
            "PAN (Optional)"
        )

        state = st.text_input(
            "State",
            value="Maharashtra"
        )

        submitted = st.form_submit_button(
            "🚀 SAVE & OPEN BUSINESS"
        )

        if submitted:

            if not business_name.strip():

                st.error("Business name is required.")

            else:

                conn = get_db()

                conn.execute("""
                    UPDATE users

                    SET
                        business_name=?,
                        business_address=?,
                        business_phone=?,
                        email=?,
                        gstin=?,
                        pan=?,
                        state=?

                    WHERE mobile=?
                """, (
                    business_name,
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

                st.session_state.business_name = business_name
                st.session_state.business_gstin = gstin

                log_action(
                    "Business Profile Created",
                    "Company"
                )

                st.success(
                    "✅ Business profile created successfully."
                )

                st.rerun()

    st.stop()


# ============================================================
# SUBSCRIPTION
# ============================================================

sub_status = subscription_status()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(f"""
<div class="card">
<b>👤 User</b><br>
{st.session_state.user_mobile}<br><br>

<b>🏢 Business</b><br>
{st.session_state.business_name}<br><br>

<b>🔐 Role</b><br>
{st.session_state.user_role}<br><br>

<b>💳 Plan</b><br>
{sub_status}
</div>
""", unsafe_allow_html=True)


if st.sidebar.button("🚪 LOGOUT"):

    st.session_state.user_mobile = None
    st.session_state.business_name = None
    st.session_state.business_gstin = None
    st.session_state.cart = []

    st.rerun()


# ============================================================
# NAVIGATION
# ============================================================

st.sidebar.markdown("### 📂 MAIN MENU")

menu = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Dashboard",
        "⚙️ Masters",
        "📦 Inventory",
        "👥 Parties",
        "🏢 Godowns",
        "🏦 Bank Accounts",
        "💰 Capital",
        "💳 Subscription",
        "⚙️ Settings"
    ]
)


# ============================================================
# HEADER
# ============================================================

st.markdown(f"""
<div class="main-header">
    <h1>{st.session_state.business_name}</h1>
    <p>
        SD TALLY BUSINESS ENTERPRISE
        • Professional Accounting Workspace
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    conn = get_db()

    mob = st.session_state.user_mobile

    sales = conn.execute("""
        SELECT COALESCE(SUM(total_amount),0)
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type IN ('Sales','Tax Invoice')
    """, (mob,)).fetchone()[0]

    purchase = conn.execute("""
        SELECT COALESCE(SUM(total_amount),0)
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
    """, (mob,)).fetchone()[0]

    receivable = conn.execute("""
        SELECT COALESCE(SUM(debit-credit),0)
        FROM ledger
        WHERE user_mobile=?
    """, (mob,)).fetchone()[0]

    stock_value = conn.execute("""
        SELECT COALESCE(
            SUM(current_stock * purchase_price),0
        )
        FROM items
        WHERE user_mobile=?
        AND is_active=1
    """, (mob,)).fetchone()[0]

    items_count = conn.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE user_mobile=?
        AND is_active=1
    """, (mob,)).fetchone()[0]

    parties_count = conn.execute("""
        SELECT COUNT(*)
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
    """, (mob,)).fetchone()[0]

    conn.close()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "💰 Total Sales",
        money(sales)
    )

    c2.metric(
        "🛒 Purchases",
        money(purchase)
    )

    c3.metric(
        "📦 Stock Value",
        money(stock_value)
    )

    c4.metric(
        "📊 Gross Difference",
        money(sales - purchase)
    )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📦 Active Items",
        items_count
    )

    c2.metric(
        "👥 Active Parties",
        parties_count
    )

    c3.metric(
        "📅 Plan",
        sub_status
    )

    st.markdown("---")

    st.subheader("⚠️ Low Stock Alert")

    conn = get_db()

    low_stock = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            current_stock AS Stock,
            min_stock AS Minimum_Stock,
            godown AS Godown
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        AND current_stock <= min_stock
        ORDER BY current_stock ASC
    """, conn, params=(mob,))

    conn.close()

    if low_stock.empty:

        st.success("✅ No low-stock items.")

    else:

        st.dataframe(
            low_stock,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# MASTERS
# ============================================================

elif menu == "⚙️ Masters":

    st.subheader("⚙️ Masters Management")

    tabs = st.tabs([
        "📦 Item Master",
        "👥 Party Master",
        "🏢 Godown Master",
        "🏦 Bank Master"
    ])

    # --------------------------------------------------------
    # ITEM MASTER
    # --------------------------------------------------------

    with tabs[0]:

        st.subheader("📦 Item Master")

        with st.form("item_form"):

            c1, c2 = st.columns(2)

            item_name = c1.text_input(
                "Item Name *"
            )

            item_code = c2.text_input(
                "Item Code"
            )

            c1, c2, c3 = st.columns(3)

            barcode = c1.text_input(
                "Barcode"
            )

            unit = c2.selectbox(
                "Unit",
                units()
            )

            category = c3.text_input(
                "Category"
            )

            c1, c2, c3 = st.columns(3)

            hsn = c1.text_input(
                "HSN / SAC"
            )

            gst = c2.selectbox(
                "GST %",
                [0, 5, 12, 18, 28]
            )

            godown = c3.text_input(
                "Godown",
                value="Main Store"
            )

            c1, c2, c3, c4 = st.columns(4)

            purchase_price = c1.number_input(
                "Purchase Price",
                min_value=0.0
            )

            sale_price = c2.number_input(
                "Sale Price",
                min_value=0.0
            )

            opening_stock = c3.number_input(
                "Opening Stock",
                min_value=0.0
            )

            min_stock = c4.number_input(
                "Minimum Stock",
                min_value=0.0,
                value=5.0
            )

            batch = st.text_input(
                "Batch Number"
            )

            expiry = st.date_input(
                "Expiry Date",
                value=None
            )

            description = st.text_area(
                "Description"
            )

            save_item = st.form_submit_button(
                "💾 SAVE ITEM"
            )

            if save_item:

                if not item_name.strip():

                    st.error(
                        "Item name is required."
                    )

                else:

                    conn = get_db()

                    conn.execute("""
                        INSERT INTO items
                        (
                            user_mobile,
                            item_name,
                            item_code,
                            barcode,
                            category,
                            unit,
                            hsn_sac,
                            gst_rate,
                            purchase_price,
                            sale_price,
                            opening_stock,
                            current_stock,
                            min_stock,
                            batch_no,
                            expiry_date,
                            godown,
                            description,
                            created_at
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        mob,
                        item_name,
                        item_code,
                        barcode,
                        category,
                        unit,
                        hsn,
                        gst,
                        purchase_price,
                        sale_price,
                        opening_stock,
                        opening_stock,
                        min_stock,
                        batch,
                        str(expiry) if expiry else "",
                        godown,
                        description,
                        now()
                    ))

                    conn.commit()
                    conn.close()

                    log_action(
                        "Item Created",
                        "Item Master",
                        item_name
                    )

                    st.success(
                        f"✅ Item '{item_name}' saved."
                    )

        st.markdown("---")

        conn = get_db()

        item_df = pd.read_sql_query("""
            SELECT
                id,
                item_name,
                item_code,
                barcode,
                unit,
                hsn_sac,
                gst_rate,
                purchase_price,
                sale_price,
                current_stock,
                godown,
                is_active
            FROM items
            WHERE user_mobile=?
            ORDER BY id DESC
        """, conn, params=(mob,))

        conn.close()

        st.dataframe(
            item_df,
            use_container_width=True,
            hide_index=True
        )


    # --------------------------------------------------------
    # PARTY MASTER
    # --------------------------------------------------------

    with tabs[1]:

        st.subheader("👥 Customer / Supplier Master")

        with st.form("party_form"):

            c1, c2 = st.columns(2)

            party_name = c1.text_input(
                "Party Name *"
            )

            party_type = c2.selectbox(
                "Party Type",
                ["Customer", "Supplier", "Both"]
            )

            c1, c2, c3 = st.columns(3)

            mobile = c1.text_input(
                "Mobile"
            )

            email = c2.text_input(
                "Email"
            )

            gstin = c3.text_input(
                "GSTIN"
            )

            address = st.text_area(
                "Address"
            )

            c1, c2, c3, c4 = st.columns(4)

            state = c1.text_input(
                "State",
                value="Maharashtra"
            )

            state_code = c2.text_input(
                "State Code",
                value="27"
            )

            opening = c3.number_input(
                "Opening Balance",
                min_value=0.0
            )

            credit_days = c4.number_input(
                "Credit Days",
                min_value=0
            )

            credit_limit = st.number_input(
                "Credit Limit",
                min_value=0.0
            )

            save_party = st.form_submit_button(
                "💾 SAVE PARTY"
            )

            if save_party:

                if not party_name.strip():

                    st.error(
                        "Party name is required."
                    )

                else:

                    conn = get_db()

                    conn.execute("""
                        INSERT INTO parties
                        (
                            user_mobile,
                            party_name,
                            party_type,
                            mobile,
                            email,
                            address,
                            gstin,
                            state,
                            state_code,
                            opening_balance,
                            credit_limit,
                            credit_days,
                            created_at
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        mob,
                        party_name,
                        party_type,
                        mobile,
                        email,
                        address,
                        gstin,
                        state,
                        state_code,
                        opening,
                        credit_limit,
                        credit_days,
                        now()
                    ))

                    conn.commit()
                    conn.close()

                    log_action(
                        "Party Created",
                        "Party Master",
                        party_name
                    )

                    st.success(
                        f"✅ Party '{party_name}' saved."
                    )

        st.markdown("---")

        conn = get_db()

        party_df = pd.read_sql_query("""
            SELECT
                id,
                party_name,
                party_type,
                mobile,
                gstin,
                state,
                opening_balance,
                credit_limit,
                credit_days,
                is_active
            FROM parties
            WHERE user_mobile=?
            ORDER BY id DESC
        """, conn, params=(mob,))

        conn.close()

        st.dataframe(
            party_df,
            use_container_width=True,
            hide_index=True
        )


    # --------------------------------------------------------
    # GODOWN MASTER
    # --------------------------------------------------------

    with tabs[2]:

        st.subheader("🏢 Godown / Warehouse Master")

        with st.form("godown_form"):

            name = st.text_input(
                "Godown Name *"
            )

            address = st.text_area(
                "Godown Address"
            )

            manager = st.text_input(
                "Manager Name"
            )

            mobile_g = st.text_input(
                "Manager Mobile"
            )

            save_godown = st.form_submit_button(
                "💾 SAVE GODOWN"
            )

            if save_godown:

                if name.strip():

                    conn = get_db()

                    conn.execute("""
                        INSERT INTO godowns
                        (
                            user_mobile,
                            godown_name,
                            address,
                            manager_name,
                            mobile,
                            created_at
                        )
                        VALUES (?,?,?,?,?,?)
                    """, (
                        mob,
                        name,
                        address,
                        manager,
                        mobile_g,
                        now()
                    ))

                    conn.commit()
                    conn.close()

                    log_action(
                        "Godown Created",
                        "Godown Master",
                        name
                    )

                    st.success(
                        f"✅ Godown '{name}' saved."
                    )

                else:

                    st.error(
                        "Godown name required."
                    )

        conn = get_db()

        godown_df = pd.read_sql_query("""
            SELECT
                id,
                godown_name,
                address,
                manager_name,
                mobile,
                is_active
            FROM godowns
            WHERE user_mobile=?
            ORDER BY id DESC
        """, conn, params=(mob,))

        conn.close()

        st.dataframe(
            godown_df,
            use_container_width=True,
            hide_index=True
        )


    # --------------------------------------------------------
    # BANK MASTER
    # --------------------------------------------------------

    with tabs[3]:

        st.subheader("🏦 Multiple Bank Accounts")

        with st.form("bank_form"):

            c1, c2 = st.columns(2)

            bank_name = c1.text_input(
                "Bank Name *"
            )

            account_name = c2.text_input(
                "Account Holder Name"
            )

            c1, c2, c3 = st.columns(3)

            account_no = c1.text_input(
                "Account Number"
            )

            ifsc = c2.text_input(
                "IFSC"
            )

            branch = c3.text_input(
                "Branch"
            )

            c1, c2 = st.columns(2)

            opening_balance = c1.number_input(
                "Opening Balance",
                min_value=0.0
            )

            upi_id = c2.text_input(
                "UPI ID"
            )

            save_bank = st.form_submit_button(
                "💾 SAVE BANK ACCOUNT"
            )

            if save_bank:

                if bank_name.strip():

                    conn = get_db()

                    conn.execute("""
                        INSERT INTO bank_accounts
                        (
                            user_mobile,
                            bank_name,
                            account_name,
                            account_no,
                            ifsc,
                            branch,
                            opening_balance,
                            current_balance,
                            upi_id,
                            created_at
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (
                        mob,
                        bank_name,
                        account_name,
                        account_no,
                        ifsc,
                        branch,
                        opening_balance,
                        opening_balance,
                        upi_id,
                        now()
                    ))

                    conn.commit()
                    conn.close()

                    log_action(
                        "Bank Account Created",
                        "Bank Master",
                        bank_name
                    )

                    st.success(
                        "✅ Bank account saved."
                    )

                else:

                    st.error(
                        "Bank name required."
                    )

        conn = get_db()

        bank_df = pd.read_sql_query("""
            SELECT
                id,
                bank_name,
                account_name,
                account_no,
                ifsc,
                branch,
                opening_balance,
                current_balance,
                upi_id,
                is_active
            FROM bank_accounts
            WHERE user_mobile=?
            ORDER BY id DESC
        """, conn, params=(mob,))

        conn.close()

        st.dataframe(
            bank_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# INVENTORY
# ============================================================

elif menu == "📦 Inventory":

    st.subheader("📦 Inventory Management")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            id,
            item_name AS Item,
            item_code AS Code,
            barcode AS Barcode,
            unit AS Unit,
            hsn_sac AS HSN_SAC,
            gst_rate AS GST,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate,
            current_stock AS Stock,
            min_stock AS Min_Stock,
            godown AS Godown,
            batch_no AS Batch,
            expiry_date AS Expiry
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info(
            "No items found. Add items from Masters."
        )

    else:

        search = st.text_input(
            "🔍 Search Item / Barcode"
        )

        if search:

            df = df[
                df["Item"].astype(str).str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                df["Barcode"].astype(str).str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PARTIES
# ============================================================

elif menu == "👥 Parties":

    st.subheader("👥 Party Ledger Master")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            party_name AS Party,
            party_type AS Type,
            mobile AS Mobile,
            gstin AS GSTIN,
            state AS State,
            opening_balance AS Opening_Balance,
            credit_limit AS Credit_Limit,
            credit_days AS Credit_Days
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# GODOWNS
# ============================================================

elif menu == "🏢 Godowns":

    st.subheader("🏢 Godown / Warehouse List")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            godown_name AS Godown,
            address AS Address,
            manager_name AS Manager,
            mobile AS Mobile
        FROM godowns
        WHERE user_mobile=?
        AND is_active=1
    """, conn, params=(mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BANK ACCOUNTS
# ============================================================

elif menu == "🏦 Bank Accounts":

    st.subheader("🏦 Bank Accounts & Balances")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            bank_name AS Bank,
            account_name AS Holder,
            account_no AS Account_Number,
            ifsc AS IFSC,
            branch AS Branch,
            opening_balance AS Opening_Balance,
            current_balance AS Current_Balance,
            upi_id AS UPI
        FROM bank_accounts
        WHERE user_mobile=?
        AND is_active=1
    """, conn, params=(mob,))

    conn.close()

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CAPITAL
# ============================================================

elif menu == "💰 Capital":

    st.subheader("💰 Capital & Drawings")

    with st.form("capital_form"):

        entry_type = st.selectbox(
            "Entry Type",
            [
                "CAPITAL INTRODUCED",
                "DRAWINGS"
            ]
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save = st.form_submit_button(
            "💾 POST CAPITAL ENTRY"
        )

        if save and amount > 0:

            conn = get_db()

            conn.execute("""
                INSERT INTO capital
                (
                    user_mobile,
                    date,
                    entry_type,
                    amount,
                    narration,
                    created_at
                )
                VALUES (?,?,?,?,?,?)
            """, (
                mob,
                today(),
                entry_type,
                amount,
                narration,
                now()
            ))

            conn.commit()
            conn.close()

            log_action(
                entry_type,
                "Capital"
            )

            st.success(
                "✅ Capital entry posted."
            )


# ============================================================
# SUBSCRIPTION
# ============================================================

elif menu == "💳 Subscription":

    st.subheader("💳 Account & Subscription")

    st.info(
        f"Current Status: **{sub_status}**"
    )

    user = get_user()

    if user:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Trial End",
            user[14] or "-"
        )

        c2.metric(
            "Paid Status",
            "ACTIVE" if user[15] else "NO"
        )

        c3.metric(
            "Paid Till",
            user[16] or "-"
        )

    st.markdown("---")

    st.markdown("""
### 🎁 Free Trial

New accounts receive a **10-day free trial**.

### 💼 Professional Subscription

Subscription infrastructure is prepared in the database.

Actual payment gateway/API can be connected later.
""")


# ============================================================
# SETTINGS
# ============================================================

elif menu == "⚙️ Settings":

    st.subheader("⚙️ Company Settings")

    user = get_user()

    with st.form("settings_form"):

        business_name = st.text_input(
            "Business Name",
            value=user[5] or ""
        )

        address = st.text_area(
            "Address",
            value=user[6] or ""
        )

        phone = st.text_input(
            "Business Phone",
            value=user[7] or ""
        )

        email = st.text_input(
            "Email",
            value=user[8] or ""
        )

        gstin = st.text_input(
            "GSTIN",
            value=user[9] or ""
        )

        pan = st.text_input(
            "PAN",
            value=user[10] or ""
        )

        state = st.text_input(
            "State",
            value=user[11] or "Maharashtra"
        )

        save = st.form_submit_button(
            "💾 UPDATE COMPANY PROFILE"
        )

        if save:

            conn = get_db()

            conn.execute("""
                UPDATE users
                SET
                    business_name=?,
                    business_address=?,
                    business_phone=?,
                    email=?,
                    gstin=?,
                    pan=?,
                    state=?
                WHERE mobile=?
            """, (
                business_name,
                address,
                phone,
                email,
                gstin,
                pan,
                state,
                mob
            ))

            conn.commit()
            conn.close()

            st.session_state.business_name = business_name
            st.session_state.business_gstin = gstin

            log_action(
                "Company Profile Updated",
                "Settings"
            )

            st.success(
                "✅ Company profile updated."
            )

            st.rerun()


# ============================================================
# STEP 1 END
# STEP 2 WILL BE PASTED BELOW THIS LINE
# ============================================================
# ============================================================
# SD TALLY BUSINESS ENTERPRISE — STEP 2A
# Advanced Accounting, Inventory, Billing & Reports
# Paste this code BELOW STEP 1
# ============================================================

# ---------- ADVANCED DATABASE TABLES ----------

def create_advanced_tables():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            entry_date TEXT,
            account_name TEXT,
            party_name TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            narration TEXT,
            reference_no TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            movement_date TEXT,
            item_name TEXT,
            godown_from TEXT,
            godown_to TEXT,
            qty REAL DEFAULT 0,
            unit TEXT,
            movement_type TEXT,
            reference_no TEXT,
            narration TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS invoice_settings (
            user_mobile TEXT PRIMARY KEY,
            invoice_prefix TEXT DEFAULT 'INV',
            next_invoice_no INTEGER DEFAULT 1,
            thermal_width INTEGER DEFAULT 80,
            currency TEXT DEFAULT 'INR',
            terms TEXT DEFAULT 'Goods once sold will not be returned.'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS subscription_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            payment_date TEXT,
            amount REAL,
            plan_name TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bank_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            import_date TEXT,
            file_name TEXT,
            total_entries INTEGER DEFAULT 0,
            status TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            user_mobile TEXT PRIMARY KEY,
            invoice_footer TEXT,
            default_gst REAL DEFAULT 18,
            default_payment_mode TEXT DEFAULT 'Cash',
            negative_stock_allowed INTEGER DEFAULT 0,
            auto_backup INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


create_advanced_tables()


# ---------- HELPER FUNCTIONS ----------

def money(value):
    try:
        return f"₹ {float(value):,.2f}"
    except Exception:
        return "₹ 0.00"


def safe_float(value, default=0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def add_ledger_entry(
    user_mobile,
    account_name,
    party_name,
    voucher_type,
    voucher_no,
    debit=0,
    credit=0,
    narration="",
    reference_no=""
):
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO ledger_entries
        (user_mobile, entry_date, account_name, party_name,
         voucher_type, voucher_no, debit, credit, narration, reference_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_mobile,
        str(datetime.now().date()),
        account_name,
        party_name,
        voucher_type,
        voucher_no,
        safe_float(debit),
        safe_float(credit),
        narration,
        reference_no
    ))

    conn.commit()
    conn.close()


def get_units():
    return [
        "PCS",
        "KG",
        "G",
        "LTR",
        "ML",
        "MTR",
        "CM",
        "MM",
        "BOX",
        "BAG",
        "PACK",
        "DOZEN",
        "SQFT",
        "SQM",
        "SET",
        "PAIR",
        "NOS"
    ]


def calculate_tax(taxable, gst_rate, interstate=False):
    taxable = safe_float(taxable)
    gst_rate = safe_float(gst_rate)

    total_tax = taxable * gst_rate / 100

    if interstate:
        return 0.0, 0.0, total_tax

    return total_tax / 2, total_tax / 2, 0.0


def generate_invoice_number(user_mobile):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "SELECT invoice_prefix, next_invoice_no FROM invoice_settings WHERE user_mobile=?",
        (user_mobile,)
    )

    row = c.fetchone()

    if not row:
        c.execute("""
            INSERT INTO invoice_settings
            (user_mobile, invoice_prefix, next_invoice_no)
            VALUES (?, 'INV', 1)
        """, (user_mobile,))
        prefix = "INV"
        number = 1
    else:
        prefix = row[0]
        number = row[1]

    invoice_no = f"{prefix}-{number:05d}"

    c.execute("""
        UPDATE invoice_settings
        SET next_invoice_no=?
        WHERE user_mobile=?
    """, (number + 1, user_mobile))

    conn.commit()
    conn.close()

    return invoice_no


def record_stock_movement(
    user_mobile,
    item_name,
    qty,
    unit,
    movement_type,
    godown_from="",
    godown_to="",
    reference_no="",
    narration=""
):
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO stock_movements
        (user_mobile, movement_date, item_name,
         godown_from, godown_to, qty, unit,
         movement_type, reference_no, narration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_mobile,
        str(datetime.now().date()),
        item_name,
        godown_from,
        godown_to,
        safe_float(qty),
        unit,
        movement_type,
        reference_no,
        narration
    ))

    conn.commit()
    conn.close()


# ============================================================
# ADVANCED APP MODULES
# ============================================================

# Add these modules to your application after the existing modules.
# ============================================================


# ---------- PROFESSIONAL UNIT MASTER ----------

if menu == "🧩 Advanced Unit Master":

    st.subheader("⚖️ Professional Unit of Measurement Master")

    units = get_units()

    unit_df = pd.DataFrame({
        "Unit Code": units,
        "Description": [
            "Pieces",
            "Kilogram",
            "Gram",
            "Litre",
            "Millilitre",
            "Metre",
            "Centimetre",
            "Millimetre",
            "Box",
            "Bag",
            "Pack",
            "Dozen",
            "Square Feet",
            "Square Metre",
            "Set",
            "Pair",
            "Numbers"
        ]
    })

    st.dataframe(
        unit_df,
        use_container_width=True,
        hide_index=True
    )


# ---------- STOCK MOVEMENT HISTORY ----------

elif menu == "📦 Advanced Stock Movement":

    st.subheader("📦 Complete Stock Movement History")

    conn = get_db()

    movement_df = pd.read_sql_query("""
        SELECT
            movement_date AS Date,
            item_name AS Item,
            godown_from AS From_Godown,
            godown_to AS To_Godown,
            qty AS Quantity,
            unit AS Unit,
            movement_type AS Movement,
            reference_no AS Reference,
            narration AS Narration
        FROM stock_movements
        WHERE user_mobile=?
        ORDER BY id DESC
    """, conn, params=(user_mob,))

    conn.close()

    if movement_df.empty:
        st.info("No stock movement records found.")
    else:
        st.dataframe(
            movement_df,
            use_container_width=True,
            hide_index=True
        )

        csv_data = movement_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Export Stock Movement Excel-Compatible CSV",
            data=csv_data,
            file_name="stock_movement_report.csv",
            mime="text/csv"
        )


# ---------- PROFESSIONAL PARTY LEDGER ----------

elif menu == "📒 Advanced Party Ledger":

    st.subheader("📒 Professional Party Ledger")

    conn = get_db()
    c = conn.cursor()

    parties = [
        r[0]
        for r in c.execute("""
            SELECT party_name
            FROM parties
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY party_name
        """, (user_mob,)).fetchall()
    ]

    if not parties:
        st.warning("Please create a Customer or Supplier first.")
    else:

        selected_party = st.selectbox(
            "Select Customer / Supplier",
            parties
        )

        ledger_df = pd.read_sql_query("""
            SELECT
                entry_date AS Date,
                voucher_type AS Voucher,
                voucher_no AS Voucher_No,
                debit AS Debit,
                credit AS Credit,
                narration AS Narration
            FROM ledger_entries
            WHERE user_mobile=?
            AND party_name=?
            ORDER BY id
        """, conn, params=(user_mob, selected_party))

        conn.close()

        if ledger_df.empty:
            st.info("No ledger transactions found.")
        else:

            ledger_df["Debit"] = pd.to_numeric(
                ledger_df["Debit"],
                errors="coerce"
            ).fillna(0)

            ledger_df["Credit"] = pd.to_numeric(
                ledger_df["Credit"],
                errors="coerce"
            ).fillna(0)

            ledger_df["Balance"] = (
                ledger_df["Debit"].cumsum()
                - ledger_df["Credit"].cumsum()
            )

            total_debit = ledger_df["Debit"].sum()
            total_credit = ledger_df["Credit"].sum()
            balance = total_debit - total_credit

            a, b, c = st.columns(3)

            a.metric("Total Debit", money(total_debit))
            b.metric("Total Credit", money(total_credit))
            c.metric("Closing Balance", money(balance))

            st.dataframe(
                ledger_df,
                use_container_width=True,
                hide_index=True
            )


# ---------- BANK STATEMENT SMART IMPORT ----------

elif menu == "🏦 Smart Bank Excel Import":

    st.subheader("🏦 Smart Bank Statement Import")

    uploaded_file = st.file_uploader(
        "Upload Bank Statement",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file:

        try:

            if uploaded_file.name.lower().endswith(".csv"):
                bank_df = pd.read_csv(uploaded_file)
            else:
                bank_df = pd.read_excel(uploaded_file)

            st.success(
                f"✅ File loaded: {uploaded_file.name}"
            )

            st.write(
                f"Total Rows: **{len(bank_df)}**"
            )

            st.dataframe(
                bank_df,
                use_container_width=True
            )

            st.markdown("### 🔄 Import Options")

            import_mode = st.selectbox(
                "Select Transaction Type",
                [
                    "Auto Detect",
                    "Deposit",
                    "Withdrawal"
                ]
            )

            if st.button("📥 Import Bank Entries"):

                conn = get_db()
                c = conn.cursor()

                imported = 0

                for _, row in bank_df.iterrows():

                    values = list(row.values)

                    date_value = (
                        str(values[0])
                        if len(values) > 0
                        else str(datetime.now().date())
                    )

                    particulars = (
                        str(values[1])
                        if len(values) > 1
                        else "Imported Bank Transaction"
                    )

                    amount = 0

                    for value in values[2:]:
                        test_amount = safe_float(value, None)

                        if test_amount is not None and test_amount != 0:
                            amount = abs(test_amount)
                            break

                    txn_type = import_mode

                    if txn_type == "Auto Detect":
                        txn_type = "DEPOSIT"

                    c.execute("""
                        INSERT INTO capital_bank_ledger
                        (user_mobile, date, account_type,
                         particulars, amount, txn_type)
                        VALUES (?, ?, 'Bank Account', ?, ?, ?)
                    """, (
                        user_mob,
                        date_value,
                        particulars,
                        amount,
                        txn_type
                    ))

                    imported += 1

                c.execute("""
                    INSERT INTO bank_imports
                    (user_mobile, import_date, file_name,
                     total_entries, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_mob,
                    str(datetime.now()),
                    uploaded_file.name,
                    imported,
                    "Imported"
                ))

                conn.commit()
                conn.close()

                st.success(
                    f"✅ {imported} bank entries imported successfully."
                )

        except Exception as e:

            st.error(
                f"❌ Unable to read bank statement: {e}"
            )


# ---------- PROFESSIONAL BACKUP & RESTORE ----------

elif menu == "☁️ Professional Backup & Restore":

    st.subheader("☁️ Professional Business Backup & Restore")

    conn = get_db()

    tables = [
        "users",
        "inventory",
        "godowns",
        "parties",
        "bank_accounts",
        "vouchers",
        "ledger_entries",
        "stock_movements",
        "capital_bank_ledger",
        "branding",
        "invoice_settings",
        "subscription_payments",
        "bank_imports",
        "app_settings"
    ]

    backup_data = {}

    for table in tables:

        try:

            df = pd.read_sql_query(
                f"SELECT * FROM {table} WHERE user_mobile=?",
                conn,
                params=(user_mob,)
            )

            backup_data[table] = df.to_dict(
                orient="records"
            )

        except Exception:
            backup_data[table] = []

    conn.close()

    backup_json = json.dumps(
        backup_data,
        indent=4,
        default=str
    )

    st.download_button(
        "📥 Download Complete Business Backup JSON",
        data=backup_json,
        file_name=f"{st.session_state.business_name}_FULL_BACKUP.json",
        mime="application/json"
    )

    st.info(
        "Keep this backup file safely. It contains your business accounting data."
    )


# ---------- PROFESSIONAL INVOICE SETTINGS ----------

elif menu == "⚙️ Invoice & Business Settings":

    st.subheader("⚙️ Invoice & Business Configuration")

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT invoice_prefix,
               next_invoice_no,
               thermal_width,
               terms
        FROM invoice_settings
        WHERE user_mobile=?
    """, (user_mob,))

    settings = c.fetchone()

    if settings:

        current_prefix = settings[0]
        current_number = settings[1]
        current_width = settings[2]
        current_terms = settings[3]

    else:

        current_prefix = "INV"
        current_number = 1
        current_width = 80
        current_terms = "Goods once sold will not be returned."

    prefix = st.text_input(
        "Invoice Prefix",
        value=current_prefix
    )

    next_no = st.number_input(
        "Next Invoice Number",
        min_value=1,
        value=int(current_number)
    )

    thermal_width = st.selectbox(
        "Thermal Printer Width",
        [58, 80],
        index=1 if current_width == 80 else 0
    )

    terms = st.text_area(
        "Invoice Terms & Conditions",
        value=current_terms
    )

    if st.button("💾 Save Invoice Settings"):

        c.execute("""
            INSERT OR REPLACE INTO invoice_settings
            (user_mobile, invoice_prefix,
             next_invoice_no, thermal_width, terms)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_mob,
            prefix,
            next_no,
            thermal_width,
            terms
        ))

        conn.commit()
        conn.close()

        st.success(
            "✅ Invoice settings saved successfully."
        )


# ---------- SUBSCRIPTION MANAGEMENT ----------

elif menu == "💳 Professional Subscription":

    st.subheader("💳 SD TALLY BUSINESS Subscription")

    st.info(
        "🎁 New users receive a 10-day free trial."
    )

    st.markdown("""
    ### Available Plans

    **FREE TRIAL**
    - 10 Days
    - Basic billing
    - Inventory
    - Party ledger
    - Reports

    **PRO**
    - Full accounting
    - GST reports
    - Thermal printing
    - WhatsApp sharing
    - Excel import/export
    - JSON backup
    - Advanced reports

    **ENTERPRISE**
    - All Pro features
    - Multiple users
    - Advanced business controls
    - Extended reporting
    """)

    plan = st.selectbox(
        "Select Subscription Plan",
        [
            "PRO Monthly",
            "PRO Yearly",
            "ENTERPRISE"
        ]
    )

    amount = {
        "PRO Monthly": 112.10,
        "PRO Yearly": 999.00,
        "ENTERPRISE": 1999.00
    }[plan]

    st.metric(
        "Selected Plan Price",
        money(amount)
    )

    transaction_id = st.text_input(
        "Payment Transaction ID / UTR"
    )

    if st.button("📤 Submit Subscription Payment"):

        conn = get_db()
        c = conn.cursor()

        c.execute("""
            INSERT INTO subscription_payments
            (user_mobile, payment_date, amount,
             plan_name, transaction_id, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
        """, (
            user_mob,
            str(datetime.now()),
            amount,
            plan,
            transaction_id
        ))

        conn.commit()
        conn.close()

        st.success(
            "✅ Subscription payment request submitted."
        )

        whatsapp_text = urllib.parse.quote(
            f"Hello, I submitted subscription payment.\n"
            f"Business: {st.session_state.business_name}\n"
            f"Plan: {plan}\n"
            f"Amount: ₹{amount}\n"
            f"Transaction ID: {transaction_id}"
        )

        st.markdown(
            f"[📲 Send Payment Details on WhatsApp]"
            f"(https://wa.me/?text={whatsapp_text})"
        )


# ---------- PROFESSIONAL DASHBOARD EXTENSION ----------

elif menu == "📊 Advanced Analytics":

    st.subheader("📊 Advanced Business Analytics")

    conn = get_db()

    sales = pd.read_sql_query("""
        SELECT
            date,
            SUM(total_amt) AS amount
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type IN ('Sales', 'Tax Invoice')
        GROUP BY date
        ORDER BY date
    """, conn, params=(user_mob,))

    purchases = pd.read_sql_query("""
        SELECT
            date,
            SUM(total_amt) AS amount
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        GROUP BY date
        ORDER BY date
    """, conn, params=(user_mob,))

    conn.close()

    total_sales = (
        sales["amount"].sum()
        if not sales.empty else 0
    )

    total_purchase = (
        purchases["amount"].sum()
        if not purchases.empty else 0
    )

    profit = total_sales - total_purchase

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Sales",
        money(total_sales)
    )

    c2.metric(
        "Purchase",
        money(total_purchase)
    )

    c3.metric(
        "Gross Difference",
        money(profit)
    )

    if not sales.empty:

        st.markdown("### 📈 Daily Sales")

        sales_chart = sales.copy()

        sales_chart["date"] = pd.to_datetime(
            sales_chart["date"],
            errors="coerce"
        )

        st.line_chart(
            sales_chart.set_index("date")["amount"]
        )

    if not purchases.empty:

        st.markdown("### 📉 Daily Purchases")

        purchase_chart = purchases.copy()

        purchase_chart["date"] = pd.to_datetime(
            purchase_chart["date"],
            errors="coerce"
        )

        st.bar_chart(
            purchase_chart.set_index("date")["amount"]
        )


# ============================================================
# END OF STEP 2A
# ============================================================
# ============================================================
# SD TALLY BUSINESS ENTERPRISE
# STEP 2B — VOUCHERS + ACCOUNTING + REPORTS
# ============================================================

# ------------------------------------------------------------
# EXTRA NAVIGATION
# ------------------------------------------------------------

st.sidebar.markdown("### 🧾 ACCOUNTING")

accounting_menu = st.sidebar.radio(
    "Select Accounting Module",
    [
        "🚫 None",
        "🧾 Sales Invoice",
        "🛒 Purchase Invoice",
        "💵 Receipt",
        "💸 Payment",
        "🔄 Contra",
        "📒 Journal",
        "📊 Ledger Report",
        "📈 Trial Balance",
        "💰 Profit & Loss",
        "📋 Day Book",
        "📦 Stock Report"
    ],
    key="accounting_navigation"
)


# ============================================================
# COMMON VOUCHER FUNCTION
# ============================================================

def calculate_gst_amount(taxable, gst_rate, party_state="Maharashtra"):
    taxable = float(taxable or 0)
    gst_rate = float(gst_rate or 0)

    gst_amount = taxable * gst_rate / 100

    if party_state == "Maharashtra":
        cgst = gst_amount / 2
        sgst = gst_amount / 2
        igst = 0
    else:
        cgst = 0
        sgst = 0
        igst = gst_amount

    return round(cgst, 2), round(sgst, 2), round(igst, 2)


def save_transaction(
    voucher_type,
    voucher_no,
    date,
    party_name,
    item_name,
    unit,
    hsn,
    qty,
    rate,
    discount,
    gst_rate,
    payment_mode,
    narration=""
):

    taxable = (float(qty) * float(rate)) - float(discount)

    if taxable < 0:
        taxable = 0

    cgst, sgst, igst = calculate_gst_amount(
        taxable,
        gst_rate
    )

    total = taxable + cgst + sgst + igst

    conn = get_db()

    conn.execute("""
        INSERT INTO transactions
        (
            user_mobile,
            voucher_type,
            voucher_no,
            date,
            party_name,
            item_name,
            unit,
            hsn_sac,
            qty,
            rate,
            discount,
            taxable_amount,
            gst_rate,
            cgst,
            sgst,
            igst,
            total_amount,
            payment_mode,
            narration,
            created_at
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        st.session_state.user_mobile,
        voucher_type,
        voucher_no,
        date,
        party_name,
        item_name,
        unit,
        hsn,
        qty,
        rate,
        discount,
        taxable,
        gst_rate,
        cgst,
        sgst,
        igst,
        total,
        payment_mode,
        narration,
        now()
    ))

    conn.commit()
    conn.close()

    return total


# ============================================================
# SALES INVOICE
# ============================================================

if accounting_menu == "🧾 Sales Invoice":

    st.subheader("🧾 Sales Invoice")

    conn = get_db()

    parties = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        AND party_type IN ('Customer','Both')
        ORDER BY party_name
    """, conn, params=(st.session_state.user_mobile,))

    items = pd.read_sql_query("""
        SELECT
            item_name,
            unit,
            hsn_sac,
            sale_price,
            gst_rate,
            current_stock
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(st.session_state.user_mobile,))

    conn.close()

    with st.form("sales_invoice_2b"):

        c1, c2, c3 = st.columns(3)

        voucher_no = c1.text_input(
            "Invoice No",
            value=f"SI-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        invoice_date = c2.date_input(
            "Invoice Date"
        )

        payment_mode = c3.selectbox(
            "Payment Mode",
            [
                "Credit",
                "Cash",
                "Bank",
                "UPI"
            ]
        )

        if not parties.empty:
            party_name = st.selectbox(
                "Customer",
                parties["party_name"].tolist()
            )
        else:
            party_name = st.text_input(
                "Customer Name"
            )

        if not items.empty:

            item_name = st.selectbox(
                "Item",
                items["item_name"].tolist()
            )

            selected = items[
                items["item_name"] == item_name
            ].iloc[0]

            unit = selected["unit"]
            hsn = selected["hsn_sac"]
            default_rate = float(
                selected["sale_price"] or 0
            )
            default_gst = float(
                selected["gst_rate"] or 0
            )

        else:

            item_name = st.text_input("Item Name")
            unit = st.selectbox("Unit", units())
            hsn = st.text_input("HSN / SAC")
            default_rate = 0
            default_gst = 0

        c1, c2, c3, c4 = st.columns(4)

        qty = c1.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0
        )

        rate = c2.number_input(
            "Rate",
            min_value=0.0,
            value=default_rate
        )

        discount = c3.number_input(
            "Discount",
            min_value=0.0
        )

        gst_rate = c4.selectbox(
            "GST %",
            [0, 5, 12, 18, 28],
            index=[0, 5, 12, 18, 28].index(
                int(default_gst)
            ) if int(default_gst) in [0,5,12,18,28] else 0
        )

        narration = st.text_area(
            "Narration"
        )

        save_sales = st.form_submit_button(
            "💾 SAVE SALES INVOICE"
        )

        if save_sales:

            if not party_name.strip():
                st.error("Customer name required.")

            elif not item_name.strip():
                st.error("Item name required.")

            elif qty <= 0:
                st.error("Quantity must be greater than zero.")

            else:

                total = save_transaction(
                    "Sales",
                    voucher_no,
                    str(invoice_date),
                    party_name,
                    item_name,
                    unit,
                    hsn,
                    qty,
                    rate,
                    discount,
                    gst_rate,
                    payment_mode,
                    narration
                )

                # STOCK OUT
                conn = get_db()

                row = conn.execute("""
                    SELECT current_stock
                    FROM items
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    st.session_state.user_mobile,
                    item_name
                )).fetchone()

                if row:

                    new_stock = float(row[0]) - qty

                    conn.execute("""
                        UPDATE items
                        SET current_stock=?
                        WHERE user_mobile=?
                        AND item_name=?
                    """, (
                        new_stock,
                        st.session_state.user_mobile,
                        item_name
                    ))

                    conn.execute("""
                        INSERT INTO stock_movements
                        (
                            user_mobile,
                            date,
                            item_name,
                            godown,
                            movement_type,
                            reference_no,
                            qty_out,
                            balance_qty,
                            rate,
                            created_at
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (
                        st.session_state.user_mobile,
                        str(invoice_date),
                        item_name,
                        "Main Store",
                        "SALES",
                        voucher_no,
                        qty,
                        new_stock,
                        rate,
                        now()
                    ))

                conn.commit()
                conn.close()

                log_action(
                    "Sales Invoice Created",
                    "Sales",
                    voucher_no
                )

                st.success(
                    f"✅ Sales Invoice Saved | Total: {money(total)}"
                )


# ============================================================
# PURCHASE INVOICE
# ============================================================

elif accounting_menu == "🛒 Purchase Invoice":

    st.subheader("🛒 Purchase Invoice")

    conn = get_db()

    parties = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        AND party_type IN ('Supplier','Both')
        ORDER BY party_name
    """, conn, params=(st.session_state.user_mobile,))

    items = pd.read_sql_query("""
        SELECT
            item_name,
            unit,
            hsn_sac,
            purchase_price,
            gst_rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(st.session_state.user_mobile,))

    conn.close()

    with st.form("purchase_invoice_2b"):

        c1, c2, c3 = st.columns(3)

        voucher_no = c1.text_input(
            "Purchase No",
            value=f"PI-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        invoice_date = c2.date_input(
            "Purchase Date"
        )

        payment_mode = c3.selectbox(
            "Payment Mode",
            [
                "Credit",
                "Cash",
                "Bank",
                "UPI"
            ]
        )

        if not parties.empty:
            party_name = st.selectbox(
                "Supplier",
                parties["party_name"].tolist()
            )
        else:
            party_name = st.text_input(
                "Supplier Name"
            )

        if not items.empty:

            item_name = st.selectbox(
                "Item",
                items["item_name"].tolist()
            )

            selected = items[
                items["item_name"] == item_name
            ].iloc[0]

            unit = selected["unit"]
            hsn = selected["hsn_sac"]
            default_rate = float(
                selected["purchase_price"] or 0
            )
            default_gst = float(
                selected["gst_rate"] or 0
            )

        else:

            item_name = st.text_input("Item Name")
            unit = st.selectbox("Unit", units())
            hsn = st.text_input("HSN / SAC")
            default_rate = 0
            default_gst = 0

        c1, c2, c3, c4 = st.columns(4)

        qty = c1.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0
        )

        rate = c2.number_input(
            "Purchase Rate",
            min_value=0.0,
            value=default_rate
        )

        discount = c3.number_input(
            "Discount",
            min_value=0.0
        )

        gst_rate = c4.selectbox(
            "GST %",
            [0, 5, 12, 18, 28],
            index=[0,5,12,18,28].index(
                int(default_gst)
            ) if int(default_gst) in [0,5,12,18,28] else 0
        )

        narration = st.text_area(
            "Narration"
        )

        save_purchase = st.form_submit_button(
            "💾 SAVE PURCHASE"
        )

        if save_purchase:

            if not party_name.strip():
                st.error("Supplier name required.")

            elif not item_name.strip():
                st.error("Item name required.")

            elif qty <= 0:
                st.error("Quantity must be greater than zero.")

            else:

                total = save_transaction(
                    "Purchase",
                    voucher_no,
                    str(invoice_date),
                    party_name,
                    item_name,
                    unit,
                    hsn,
                    qty,
                    rate,
                    discount,
                    gst_rate,
                    payment_mode,
                    narration
                )

                conn = get_db()

                row = conn.execute("""
                    SELECT current_stock
                    FROM items
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    st.session_state.user_mobile,
                    item_name
                )).fetchone()

                if row:

                    new_stock = float(row[0]) + qty

                    conn.execute("""
                        UPDATE items
                        SET current_stock=?
                        WHERE user_mobile=?
                        AND item_name=?
                    """, (
                        new_stock,
                        st.session_state.user_mobile,
                        item_name
                    ))

                    conn.execute("""
                        INSERT INTO stock_movements
                        (
                            user_mobile,
                            date,
                            item_name,
                            godown,
                            movement_type,
                            reference_no,
                            qty_in,
                            balance_qty,
                            rate,
                            created_at
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (
                        st.session_state.user_mobile,
                        str(invoice_date),
                        item_name,
                        "Main Store",
                        "PURCHASE",
                        voucher_no,
                        qty,
                        new_stock,
                        rate,
                        now()
                    ))

                conn.commit()
                conn.close()

                log_action(
                    "Purchase Invoice Created",
                    "Purchase",
                    voucher_no
                )

                st.success(
                    f"✅ Purchase Saved | Total: {money(total)}"
                )


# ============================================================
# RECEIPT
# ============================================================

elif accounting_menu == "💵 Receipt":

    st.subheader("💵 Receipt Voucher")

    with st.form("receipt_form_2b"):

        voucher_no = st.text_input(
            "Receipt No",
            value=f"RV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        date = st.date_input("Date")

        party = st.text_input(
            "Received From"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        mode = st.selectbox(
            "Payment Mode",
            ["Cash", "Bank", "UPI"]
        )

        narration = st.text_area(
            "Narration"
        )

        save = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save:

            if amount <= 0:
                st.error("Enter valid amount.")

            else:

                conn = get_db()

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(date),
                    party,
                    "Party",
                    "Receipt",
                    voucher_no,
                    narration,
                    0,
                    amount,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Receipt Created",
                    "Receipt",
                    voucher_no
                )

                st.success(
                    f"✅ Receipt saved: {money(amount)}"
                )


# ============================================================
# PAYMENT
# ============================================================

elif accounting_menu == "💸 Payment":

    st.subheader("💸 Payment Voucher")

    with st.form("payment_form_2b"):

        voucher_no = st.text_input(
            "Payment No",
            value=f"PV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        date = st.date_input("Date")

        party = st.text_input(
            "Paid To"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        mode = st.selectbox(
            "Payment Mode",
            ["Cash", "Bank", "UPI"]
        )

        narration = st.text_area(
            "Narration"
        )

        save = st.form_submit_button(
            "💾 SAVE PAYMENT"
        )

        if save:

            if amount <= 0:
                st.error("Enter valid amount.")

            else:

                conn = get_db()

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(date),
                    party,
                    "Party",
                    "Payment",
                    voucher_no,
                    narration,
                    amount,
                    0,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Payment Created",
                    "Payment",
                    voucher_no
                )

                st.success(
                    f"✅ Payment saved: {money(amount)}"
                )


# ============================================================
# CONTRA
# ============================================================

elif accounting_menu == "🔄 Contra":

    st.subheader("🔄 Contra Voucher")

    with st.form("contra_form_2b"):

        voucher_no = st.text_input(
            "Contra No",
            value=f"CV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        date = st.date_input("Date")

        from_account = st.text_input(
            "From Account"
        )

        to_account = st.text_input(
            "To Account"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save = st.form_submit_button(
            "💾 SAVE CONTRA"
        )

        if save:

            if amount <= 0:
                st.error("Enter valid amount.")

            else:

                conn = get_db()

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(date),
                    to_account,
                    "Bank/Cash",
                    "Contra",
                    voucher_no,
                    f"From {from_account} - {narration}",
                    amount,
                    0,
                    now()
                ))

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(date),
                    from_account,
                    "Bank/Cash",
                    "Contra",
                    voucher_no,
                    f"To {to_account} - {narration}",
                    0,
                    amount,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Contra Created",
                    "Contra",
                    voucher_no
                )

                st.success("✅ Contra voucher saved.")


# ============================================================
# JOURNAL
# ============================================================

elif accounting_menu == "📒 Journal":

    st.subheader("📒 Journal Voucher")

    with st.form("journal_form_2b"):

        voucher_no = st.text_input(
            "Journal No",
            value=f"JV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        date = st.date_input("Date")

        account_name = st.text_input(
            "Account Name"
        )

        debit = st.number_input(
            "Debit",
            min_value=0.0
        )

        credit = st.number_input(
            "Credit",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save = st.form_submit_button(
            "💾 SAVE JOURNAL"
        )

        if save:

            if debit == 0 and credit == 0:
                st.error("Enter Debit or Credit amount.")

            else:

                conn = get_db()

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(date),
                    account_name,
                    "General",
                    "Journal",
                    voucher_no,
                    narration,
                    debit,
                    credit,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Journal Created",
                    "Journal",
                    voucher_no
                )

                st.success("✅ Journal entry saved.")


# ============================================================
# LEDGER REPORT
# ============================================================

elif accounting_menu == "📊 Ledger Report":

    st.subheader("📊 Ledger Report")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            account_name AS Account,
            voucher_type AS Voucher,
            voucher_no AS Voucher_No,
            particulars AS Particulars,
            debit AS Debit,
            credit AS Credit
        FROM ledger
        WHERE user_mobile=?
        ORDER BY date DESC, id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:
        st.info("No ledger entries found.")

    else:

        df["Balance"] = (
            df["Debit"].fillna(0)
            -
            df["Credit"].fillna(0)
        ).cumsum()

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Net Ledger Balance",
            money(df["Balance"].iloc[-1])
        )


# ============================================================
# TRIAL BALANCE
# ============================================================

elif accounting_menu == "📈 Trial Balance":

    st.subheader("📈 Trial Balance")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            account_name AS Account,
            SUM(debit) AS Debit,
            SUM(credit) AS Credit
        FROM ledger
        WHERE user_mobile=?
        GROUP BY account_name
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if df.empty:
        st.info("No accounting data available.")

    else:

        df["Debit"] = df["Debit"].fillna(0)
        df["Credit"] = df["Credit"].fillna(0)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Debit",
            money(df["Debit"].sum())
        )

        c2.metric(
            "Total Credit",
            money(df["Credit"].sum())
        )


# ============================================================
# PROFIT & LOSS
# ============================================================

elif accounting_menu == "💰 Profit & Loss":

    st.subheader("💰 Profit & Loss")

    conn = get_db()

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

    expenses = conn.execute("""
        SELECT COALESCE(SUM(amount),0)
        FROM expenses
        WHERE user_mobile=?
    """, (mob,)).fetchone()[0]

    conn.close()

    gross_profit = sales - purchase
    net_profit = gross_profit - expenses

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Sales",
        money(sales)
    )

    c2.metric(
        "Purchase",
        money(purchase)
    )

    c3.metric(
        "Expenses",
        money(expenses)
    )

    c4.metric(
        "Net Profit",
        money(net_profit)
    )

    st.markdown("---")

    st.write(
        f"**Gross Profit / Loss:** {money(gross_profit)}"
    )

    st.write(
        f"**Net Profit / Loss:** {money(net_profit)}"
    )


# ============================================================
# DAY BOOK
# ============================================================

elif accounting_menu == "📋 Day Book":

    st.subheader("📋 Day Book")

    selected_date = st.date_input(
        "Select Date",
        datetime.now().date()
    )

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher,
            voucher_no AS Voucher_No,
            party_name AS Party,
            item_name AS Item,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND date=?
        ORDER BY id DESC
    """, conn, params=(mob, str(selected_date)))

    conn.close()

    if df.empty:
        st.info("No transactions for selected date.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Transaction Value",
            money(df["Amount"].sum())
        )


# ============================================================
# STOCK REPORT
# ============================================================

elif accounting_menu == "📦 Stock Report":

    st.subheader("📦 Stock Report")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            item_code AS Code,
            unit AS Unit,
            current_stock AS Stock,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate,
            current_stock * purchase_price AS Stock_Value,
            min_stock AS Minimum_Stock,
            godown AS Godown
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("No stock data available.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Stock Value",
            money(df["Stock_Value"].sum())
        )


# ============================================================
# STEP 2B END
# ============================================================
# ============================================================
# STEP 3 — VOUCHERS + ACCOUNTING
# ============================================================

elif menu == "🧾 Vouchers":

    st.subheader("🧾 Voucher Entry")

    voucher_type = st.selectbox(
        "Voucher Type",
        [
            "Sales",
            "Purchase",
            "Receipt",
            "Payment",
            "Sales Return",
            "Purchase Return",
            "Journal",
            "Contra"
        ]
    )

    voucher_date = st.date_input(
        "Date",
        value=datetime.now().date()
    )

    voucher_no = st.text_input(
        "Voucher Number",
        value=f"V-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    # --------------------------------------------------------
    # SALES / PURCHASE
    # --------------------------------------------------------

    if voucher_type in ["Sales", "Purchase",
                        "Sales Return", "Purchase Return"]:

        conn = get_db()

        parties = pd.read_sql_query("""
            SELECT party_name
            FROM parties
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY party_name
        """, conn, params=(mob,))

        items = pd.read_sql_query("""
            SELECT
                item_name,
                unit,
                hsn_sac,
                gst_rate,
                sale_price,
                purchase_price,
                current_stock
            FROM items
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY item_name
        """, conn, params=(mob,))

        conn.close()

        party_list = (
            parties["party_name"].tolist()
            if not parties.empty else []
        )

        item_list = (
            items["item_name"].tolist()
            if not items.empty else []
        )

        party_name = st.selectbox(
            "Party",
            party_list if party_list else ["No Party Found"]
        )

        item_name = st.selectbox(
            "Item",
            item_list if item_list else ["No Item Found"]
        )

        selected_item = items[
            items["item_name"] == item_name
        ]

        if not selected_item.empty:

            item_row = selected_item.iloc[0]

            unit = item_row["unit"]
            hsn_sac = item_row["hsn_sac"]
            gst_rate = float(item_row["gst_rate"])

            if voucher_type in ["Sales", "Sales Return"]:

                default_rate = float(
                    item_row["sale_price"]
                )

            else:

                default_rate = float(
                    item_row["purchase_price"]
                )

            current_stock = float(
                item_row["current_stock"]
            )

        else:

            unit = "PCS"
            hsn_sac = ""
            gst_rate = 0
            default_rate = 0
            current_stock = 0

        c1, c2, c3 = st.columns(3)

        qty = c1.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0
        )

        rate = c2.number_input(
            "Rate",
            min_value=0.0,
            value=default_rate
        )

        discount = c3.number_input(
            "Discount",
            min_value=0.0,
            value=0.0
        )

        taxable = max(
            (qty * rate) - discount,
            0
        )

        # ----------------------------------------------------
        # GST CALCULATION
        # ----------------------------------------------------

        gst_amount = taxable * gst_rate / 100

        cgst = gst_amount / 2
        sgst = gst_amount / 2
        igst = 0.0

        total = taxable + cgst + sgst

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Taxable",
            money(taxable)
        )

        c2.metric(
            "CGST",
            money(cgst)
        )

        c3.metric(
            "SGST",
            money(sgst)
        )

        c4.metric(
            "Grand Total",
            money(total)
        )

        payment_mode = st.selectbox(
            "Payment Mode",
            [
                "Credit",
                "Cash",
                "Bank",
                "UPI"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        if st.button(
            "💾 POST VOUCHER",
            type="primary"
        ):

            if item_name == "No Item Found":

                st.error(
                    "Please create an Item first."
                )

            else:

                conn = get_db()

                # ------------------------------------------------
                # SAVE TRANSACTION
                # ------------------------------------------------

                conn.execute("""
                    INSERT INTO transactions
                    (
                        user_mobile,
                        voucher_type,
                        voucher_no,
                        date,
                        party_name,
                        item_name,
                        unit,
                        hsn_sac,
                        qty,
                        rate,
                        discount,
                        taxable_amount,
                        gst_rate,
                        cgst,
                        sgst,
                        igst,
                        total_amount,
                        payment_mode,
                        narration,
                        created_at
                    )
                    VALUES
                    (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    voucher_type,
                    voucher_no,
                    str(voucher_date),
                    party_name,
                    item_name,
                    unit,
                    hsn_sac,
                    qty,
                    rate,
                    discount,
                    taxable,
                    gst_rate,
                    cgst,
                    sgst,
                    igst,
                    total,
                    payment_mode,
                    narration,
                    now()
                ))

                # ------------------------------------------------
                # STOCK UPDATE
                # ------------------------------------------------

                if voucher_type in [
                    "Sales",
                    "Sales Return"
                ]:

                    if voucher_type == "Sales":

                        new_stock = current_stock - qty

                        qty_in = 0
                        qty_out = qty

                    else:

                        new_stock = current_stock + qty

                        qty_in = qty
                        qty_out = 0

                else:

                    if voucher_type == "Purchase":

                        new_stock = current_stock + qty

                        qty_in = qty
                        qty_out = 0

                    else:

                        new_stock = current_stock - qty

                        qty_in = 0
                        qty_out = qty

                conn.execute("""
                    UPDATE items
                    SET current_stock=?
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    new_stock,
                    mob,
                    item_name
                ))

                # ------------------------------------------------
                # STOCK MOVEMENT
                # ------------------------------------------------

                conn.execute("""
                    INSERT INTO stock_movements
                    (
                        user_mobile,
                        date,
                        item_name,
                        godown,
                        movement_type,
                        reference_no,
                        qty_in,
                        qty_out,
                        balance_qty,
                        rate,
                        created_at
                    )
                    VALUES
                    (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(voucher_date),
                    item_name,
                    "Main Store",
                    voucher_type,
                    voucher_no,
                    qty_in,
                    qty_out,
                    new_stock,
                    rate,
                    now()
                ))

                # ------------------------------------------------
                # LEDGER ENTRY
                # ------------------------------------------------

                if voucher_type in [
                    "Sales",
                    "Sales Return"
                ]:

                    account_name = party_name

                    if voucher_type == "Sales":

                        debit = total
                        credit = 0

                    else:

                        debit = 0
                        credit = total

                else:

                    account_name = party_name

                    if voucher_type == "Purchase":

                        debit = 0
                        credit = total

                    else:

                        debit = total
                        credit = 0

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        balance,
                        created_at
                    )
                    VALUES
                    (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(voucher_date),
                    account_name,
                    "Party",
                    voucher_type,
                    voucher_no,
                    item_name,
                    debit,
                    credit,
                    debit - credit,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    f"{voucher_type} Posted",
                    "Vouchers",
                    voucher_no
                )

                st.success(
                    f"✅ {voucher_type} voucher posted successfully."
                )

                st.info(
                    f"Voucher: {voucher_no} | "
                    f"Total: {money(total)}"
                )

    # --------------------------------------------------------
    # RECEIPT / PAYMENT
    # --------------------------------------------------------

    elif voucher_type in [
        "Receipt",
        "Payment"
    ]:

        conn = get_db()

        parties = pd.read_sql_query("""
            SELECT party_name
            FROM parties
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY party_name
        """, conn, params=(mob,))

        banks = pd.read_sql_query("""
            SELECT bank_name
            FROM bank_accounts
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY bank_name
        """, conn, params=(mob,))

        conn.close()

        party_list = (
            parties["party_name"].tolist()
            if not parties.empty else []
        )

        bank_list = (
            banks["bank_name"].tolist()
            if not banks.empty else []
        )

        party_name = st.selectbox(
            "Party",
            party_list if party_list
            else ["No Party Found"]
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        payment_mode = st.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI"
            ]
        )

        bank_name = ""

        if payment_mode in ["Bank", "UPI"]:

            bank_name = st.selectbox(
                "Bank Account",
                bank_list if bank_list
                else ["No Bank Account"]
            )

        narration = st.text_area(
            "Narration"
        )

        if st.button(
            f"💾 POST {voucher_type.upper()}",
            type="primary"
        ):

            if amount <= 0:

                st.error(
                    "Amount must be greater than zero."
                )

            else:

                conn = get_db()

                conn.execute("""
                    INSERT INTO transactions
                    (
                        user_mobile,
                        voucher_type,
                        voucher_no,
                        date,
                        party_name,
                        total_amount,
                        payment_mode,
                        debit_account,
                        credit_account,
                        narration,
                        created_at
                    )
                    VALUES
                    (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    voucher_type,
                    voucher_no,
                    str(voucher_date),
                    party_name,
                    amount,
                    payment_mode,
                    party_name if voucher_type == "Receipt"
                    else payment_mode,
                    payment_mode if voucher_type == "Receipt"
                    else party_name,
                    narration,
                    now()
                ))

                if voucher_type == "Receipt":

                    debit = 0
                    credit = amount

                else:

                    debit = amount
                    credit = 0

                conn.execute("""
                    INSERT INTO ledger
                    (
                        user_mobile,
                        date,
                        account_name,
                        account_type,
                        voucher_type,
                        voucher_no,
                        particulars,
                        debit,
                        credit,
                        balance,
                        created_at
                    )
                    VALUES
                    (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                                mob,
            str(voucher_date),
            party_name,
            "Party",
            voucher_type,
            voucher_no,
            narration,
            debit,
            credit,
            balance,
            now()
        ))

        conn.commit()

    except Exception as e:
        st.error(f"Ledger Error: {e}")


# ============================================================
# STEP 2B END
# ============================================================

st.markdown("---")

st.caption(
    "SD TALLY BUSINESS ENTERPRISE • "
    "Vouchers + Accounting + Reports"
)
# ============================================================
# STEP 3A — VOUCHER CENTER
# SALES • PURCHASE • RECEIPT • PAYMENT • CONTRA • JOURNAL
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧾 VOUCHER CENTER")

voucher_menu = st.sidebar.selectbox(
    "Select Voucher",
    [
        "None",
        "🧾 Sales Invoice",
        "🛒 Purchase",
        "💰 Receipt",
        "💸 Payment",
        "🔄 Contra",
        "📒 Journal"
    ],
    key="step3_voucher_menu"
)


# ============================================================
# COMMON VOUCHER FUNCTION
# ============================================================

def next_voucher_no(voucher_type):

    conn = get_db()

    row = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type=?
    """, (
        st.session_state.user_mobile,
        voucher_type
    )).fetchone()

    conn.close()

    number = (row[0] or 0) + 1

    prefix = {
        "Sales": "SI",
        "Purchase": "PI",
        "Receipt": "RC",
        "Payment": "PY",
        "Contra": "CT",
        "Journal": "JV"
    }.get(voucher_type, "VCH")

    return f"{prefix}-{number:05d}"


def save_transaction(
    voucher_type,
    voucher_no,
    voucher_date,
    party_name,
    item_name,
    unit,
    hsn_sac,
    qty,
    rate,
    discount,
    taxable_amount,
    gst_rate,
    cgst,
    sgst,
    igst,
    total_amount,
    payment_mode,
    debit_account,
    credit_account,
    narration
):

    conn = get_db()

    conn.execute("""
        INSERT INTO transactions
        (
            user_mobile,
            voucher_type,
            voucher_no,
            date,
            party_name,
            item_name,
            unit,
            hsn_sac,
            qty,
            rate,
            discount,
            taxable_amount,
            gst_rate,
            cgst,
            sgst,
            igst,
            total_amount,
            payment_mode,
            debit_account,
            credit_account,
            narration,
            created_at
        )
        VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        st.session_state.user_mobile,
        voucher_type,
        voucher_no,
        str(voucher_date),
        party_name,
        item_name,
        unit,
        hsn_sac,
        qty,
        rate,
        discount,
        taxable_amount,
        gst_rate,
        cgst,
        sgst,
        igst,
        total_amount,
        payment_mode,
        debit_account,
        credit_account,
        narration,
        now()
    ))

    conn.commit()
    conn.close()


# ============================================================
# SALES INVOICE
# ============================================================

if voucher_menu == "🧾 Sales Invoice":

    st.header("🧾 Sales Invoice")

    voucher_no = next_voucher_no("Sales")

    st.info(f"Voucher No: **{voucher_no}**")

    with st.form("sales_invoice_form"):

        c1, c2, c3 = st.columns(3)

        voucher_date = c1.date_input(
            "Invoice Date",
            value=datetime.now().date()
        )

        party_name = c2.text_input(
            "Customer Name *"
        )

        payment_mode = c3.selectbox(
            "Payment Mode",
            [
                "Credit",
                "Cash",
                "Bank",
                "UPI"
            ]
        )

        st.markdown("### 📦 Item Details")

        c1, c2, c3, c4 = st.columns(4)

        item_name = c1.text_input(
            "Item Name *"
        )

        qty = c2.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0
        )

        rate = c3.number_input(
            "Rate",
            min_value=0.0
        )

        gst_rate = c4.selectbox(
            "GST %",
            [0, 5, 12, 18, 28]
        )

        c1, c2 = st.columns(2)

        discount = c1.number_input(
            "Discount",
            min_value=0.0
        )

        hsn_sac = c2.text_input(
            "HSN / SAC"
        )

        narration = st.text_area(
            "Narration"
        )

        save_sales = st.form_submit_button(
            "💾 SAVE SALES INVOICE"
        )

        if save_sales:

            if not party_name.strip():

                st.error("Customer name is required.")

            elif not item_name.strip():

                st.error("Item name is required.")

            elif qty <= 0:

                st.error("Quantity must be greater than zero.")

            elif rate <= 0:

                st.error("Rate must be greater than zero.")

            else:

                gross = qty * rate

                taxable = max(
                    gross - discount,
                    0
                )

                if gst_rate > 0:

                    cgst = taxable * gst_rate / 200
                    sgst = taxable * gst_rate / 200
                    igst = 0

                else:

                    cgst = 0
                    sgst = 0
                    igst = 0

                total = taxable + cgst + sgst + igst

                save_transaction(
                    "Sales",
                    voucher_no,
                    voucher_date,
                    party_name,
                    item_name,
                    "PCS",
                    hsn_sac,
                    qty,
                    rate,
                    discount,
                    taxable,
                    gst_rate,
                    cgst,
                    sgst,
                    igst,
                    total,
                    payment_mode,
                    party_name,
                    "Sales",
                    narration
                )

                log_action(
                    "Sales Invoice Created",
                    "Sales",
                    voucher_no
                )

                st.success(
                    f"✅ Sales Invoice {voucher_no} saved."
                )

                st.metric(
                    "Invoice Total",
                    money(total)
                )


# ============================================================
# PURCHASE
# ============================================================

elif voucher_menu == "🛒 Purchase":

    st.header("🛒 Purchase Voucher")

    voucher_no = next_voucher_no("Purchase")

    st.info(f"Voucher No: **{voucher_no}**")

    with st.form("purchase_form"):

        c1, c2, c3 = st.columns(3)

        voucher_date = c1.date_input(
            "Purchase Date",
            value=datetime.now().date()
        )

        party_name = c2.text_input(
            "Supplier Name *"
        )

        payment_mode = c3.selectbox(
            "Payment Mode",
            [
                "Credit",
                "Cash",
                "Bank",
                "UPI"
            ],
            key="purchase_payment_mode"
        )

        c1, c2, c3, c4 = st.columns(4)

        item_name = c1.text_input(
            "Item Name *",
            key="purchase_item"
        )

        qty = c2.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0,
            key="purchase_qty"
        )

        rate = c3.number_input(
            "Purchase Rate",
            min_value=0.0,
            key="purchase_rate"
        )

        gst_rate = c4.selectbox(
            "GST %",
            [0, 5, 12, 18, 28],
            key="purchase_gst"
        )

        discount = st.number_input(
            "Discount",
            min_value=0.0,
            key="purchase_discount"
        )

        hsn_sac = st.text_input(
            "HSN / SAC",
            key="purchase_hsn"
        )

        narration = st.text_area(
            "Narration",
            key="purchase_narration"
        )

        save_purchase = st.form_submit_button(
            "💾 SAVE PURCHASE"
        )

        if save_purchase:

            if not party_name.strip():

                st.error("Supplier name is required.")

            elif not item_name.strip():

                st.error("Item name is required.")

            elif qty <= 0 or rate <= 0:

                st.error(
                    "Quantity and rate must be greater than zero."
                )

            else:

                gross = qty * rate

                taxable = max(
                    gross - discount,
                    0
                )

                cgst = taxable * gst_rate / 200
                sgst = taxable * gst_rate / 200
                igst = 0

                total = taxable + cgst + sgst

                save_transaction(
                    "Purchase",
                    voucher_no,
                    voucher_date,
                    party_name,
                    item_name,
                    "PCS",
                    hsn_sac,
                    qty,
                    rate,
                    discount,
                    taxable,
                    gst_rate,
                    cgst,
                    sgst,
                    igst,
                    total,
                    payment_mode,
                    "Purchase",
                    party_name,
                    narration
                )

                log_action(
                    "Purchase Created",
                    "Purchase",
                    voucher_no
                )

                st.success(
                    f"✅ Purchase {voucher_no} saved."
                )

                st.metric(
                    "Purchase Total",
                    money(total)
                )


# ============================================================
# RECEIPT
# ============================================================

elif voucher_menu == "💰 Receipt":

    st.header("💰 Receipt Voucher")

    voucher_no = next_voucher_no("Receipt")

    st.info(f"Voucher No: **{voucher_no}**")

    with st.form("receipt_form"):

        voucher_date = st.date_input(
            "Receipt Date",
            value=datetime.now().date()
        )

        party_name = st.text_input(
            "Received From *"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        payment_mode = st.selectbox(
            "Received Through",
            [
                "Cash",
                "Bank",
                "UPI"
            ],
            key="receipt_mode"
        )

        narration = st.text_area(
            "Narration"
        )

        save_receipt = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save_receipt:

            if not party_name.strip():

                st.error("Party name is required.")

            elif amount <= 0:

                st.error("Enter valid amount.")

            else:

                save_transaction(
                    "Receipt",
                    voucher_no,
                    voucher_date,
                    party_name,
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    amount,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    payment_mode,
                    payment_mode,
                    party_name,
                    narration
                )

                log_action(
                    "Receipt Created",
                    "Receipt",
                    voucher_no
                )

                st.success(
                    f"✅ Receipt {voucher_no} saved."
                )


# ============================================================
# PAYMENT
# ============================================================

elif voucher_menu == "💸 Payment":

    st.header("💸 Payment Voucher")

    voucher_no = next_voucher_no("Payment")

    st.info(f"Voucher No: **{voucher_no}**")

    with st.form("payment_form"):

        voucher_date = st.date_input(
            "Payment Date",
            value=datetime.now().date()
        )

        party_name = st.text_input(
            "Paid To *"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        payment_mode = st.selectbox(
            "Paid Through",
            [
                "Cash",
                "Bank",
                "UPI"
            ],
            key="payment_mode"
        )

        narration = st.text_area(
            "Narration",
            key="payment_narration"
        )

        save_payment = st.form_submit_button(
            "💾 SAVE PAYMENT"
        )

        if save_payment:

            if not party_name.strip():

                st.error("Party name is required.")

            elif amount <= 0:

                st.error("Enter valid amount.")

            else:

                save_transaction(
                    "Payment",
                    voucher_no,
                    voucher_date,
                    party_name,
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    amount,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    payment_mode,
                    party_name,
                    payment_mode,
                    narration
                )

                log_action(
                    "Payment Created",
                    "Payment",
                    voucher_no
                )

                st.success(
                    f"✅ Payment {voucher_no} saved."
                )


# ============================================================
# CONTRA
# ============================================================

elif voucher_menu == "🔄 Contra":

    st.header("🔄 Contra Voucher")

    voucher_no = next_voucher_no("Contra")

    st.info(f"Voucher No: **{voucher_no}**")

    with st.form("contra_form"):

        voucher_date = st.date_input(
            "Contra Date",
            value=datetime.now().date()
        )

        from_account = st.text_input(
            "From Account *",
            placeholder="Cash"
        )

        to_account = st.text_input(
            "To Account *",
            placeholder="Bank"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save_contra = st.form_submit_button(
            "💾 SAVE CONTRA"
        )

        if save_contra:

            if not from_account.strip():

                st.error("From Account is required.")

            elif not to_account.strip():

                st.error("To Account is required.")

            elif amount <= 0:

                st.error("Enter valid amount.")

            else:

                save_transaction(
                    "Contra",
                    voucher_no,
                    voucher_date,
                    "",
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    amount,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    "Internal Transfer",
                    to_account,
                    from_account,
                    narration
                )

                log_action(
                    "Contra Created",
                    "Contra",
                    voucher_no
                )

                st.success(
                    f"✅ Contra {voucher_no} saved."
                )


# ============================================================
# JOURNAL
# ============================================================

elif voucher_menu == "📒 Journal":

    st.header("📒 Journal Voucher")

    voucher_no = next_voucher_no("Journal")

    st.info(f"Voucher No: **{voucher_no}**")

    with st.form("journal_form"):

        voucher_date = st.date_input(
            "Journal Date",
            value=datetime.now().date()
        )

        debit_account = st.text_input(
            "Debit Account *"
        )

        credit_account = st.text_input(
            "Credit Account *"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save_journal = st.form_submit_button(
            "💾 SAVE JOURNAL"
        )

        if save_journal:

            if not debit_account.strip():

                st.error("Debit Account is required.")

            elif not credit_account.strip():

                st.error("Credit Account is required.")

            elif amount <= 0:

                st.error("Enter valid amount.")

            else:

                save_transaction(
                    "Journal",
                    voucher_no,
                    voucher_date,
                    "",
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    amount,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    "Journal",
                    debit_account,
                    credit_account,
                    narration
                )

                log_action(
                    "Journal Created",
                    "Journal",
                    voucher_no
                )

                st.success(
                    f"✅ Journal {voucher_no} saved."
                )


# ============================================================
# STEP 3A END
# ============================================================

st.markdown("---")

st.caption(
    "SD TALLY BUSINESS ENTERPRISE • "
    "STEP 3A • VOUCHER CENTER"
)
