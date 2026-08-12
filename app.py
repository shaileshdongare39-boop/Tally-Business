import streamlit as st
import pandas as pd
import sqlite3
import random
import io
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ============================================================
# SD TALLY BUSINESS - PROFESSIONAL ALL-IN-ONE APP
# ============================================================

st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "sd_tally_business.db"


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
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            mobile TEXT PRIMARY KEY,
            name TEXT DEFAULT 'Business User',
            business_name TEXT,
            business_address TEXT,
            gstin TEXT DEFAULT '',
            reg_date TEXT,
            trial_end_date TEXT,
            is_paid INTEGER DEFAULT 0,
            paid_till TEXT,
            role TEXT DEFAULT 'Owner',
            active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            item_name TEXT NOT NULL,
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS godowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            godown_name TEXT NOT NULL,
            address TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            party_name TEXT NOT NULL,
            gstin TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            party_type TEXT DEFAULT 'Customer',
            opening_balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            account_no TEXT DEFAULT '',
            ifsc_code TEXT DEFAULT '',
            branch_name TEXT DEFAULT '',
            opening_balance REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            voucher_type TEXT NOT NULL,
            voucher_no TEXT NOT NULL,
            date TEXT NOT NULL,
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            date TEXT NOT NULL,
            payment_type TEXT NOT NULL,
            party_name TEXT DEFAULT '',
            amount REAL DEFAULT 0,
            mode TEXT DEFAULT 'Cash',
            narration TEXT DEFAULT ''
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT NOT NULL,
            date TEXT NOT NULL,
            bank_name TEXT DEFAULT '',
            txn_type TEXT NOT NULL,
            amount REAL DEFAULT 0,
            narration TEXT DEFAULT ''
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS branding (
            user_mobile TEXT PRIMARY KEY,
            logo_base64 TEXT DEFAULT '',
            signature_base64 TEXT DEFAULT ''
        )
    """)

    conn.commit()

    # Compatibility with old database versions
    add_column_if_missing(conn, "users", "business_address", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "users", "gstin", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "users", "role", "TEXT DEFAULT 'Owner'")
    add_column_if_missing(conn, "users", "active", "INTEGER DEFAULT 1")

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
    "business_address": "",
    "business_gstin": "",
    "otp_sent": False,
    "generated_otp": None,
    "otp_mobile": "",
    "cart_items": [],
    "edit_item_id": None,
    "edit_party_id": None,
    "edit_godown_id": None,
    "edit_voucher_id": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
}

.stApp {
    background: #f6f8fb;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e5e7eb;
}

[data-testid="stSidebar"] * {
    color: #0f172a !important;
}

.main-header {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 22px;
    box-shadow: 0 5px 18px rgba(0,0,0,.12);
}

.main-header h1 {
    color: #38bdf8 !important;
    margin: 0;
    font-size: 2rem;
}

.main-header p {
    color: #cbd5e1 !important;
    margin: 5px 0 0;
}

.user-card {
    background: #f1f5f9;
    padding: 15px;
    border-radius: 12px;
    border-left: 5px solid #0284c7;
    margin-bottom: 12px;
}

.plan-card {
    background: #e0f2fe;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 15px;
}

.profile-card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 3px 10px rgba(0,0,0,.06);
}

.stButton > button {
    min-height: 46px;
    border-radius: 9px;
    font-weight: 700;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
}

h1,h2,h3 {
    color: #0f172a !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def money(value):
    try:
        return f"₹ {float(value):,.2f}"
    except Exception:
        return "₹ 0.00"


def load_user(mobile):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE mobile=?",
        (mobile,)
    ).fetchone()
    conn.close()
    return row


def refresh_user_session():
    if not st.session_state.user_mobile:
        return

    user = load_user(st.session_state.user_mobile)

    if user:
        st.session_state.user_role = user["role"] or "Owner"
        st.session_state.business_name = user["business_name"] or ""
        st.session_state.business_address = user["business_address"] or ""
        st.session_state.business_gstin = user["gstin"] or ""


def subscription_status(mobile):
    user = load_user(mobile)

    if not user:
        return "NEW_USER"

    today = datetime.now().date()

    if user["is_paid"] == 1 and user["paid_till"]:
        try:
            paid_till = datetime.strptime(
                user["paid_till"], "%Y-%m-%d"
            ).date()

            if today <= paid_till:
                return f"ACTIVE PRO • Till {paid_till.strftime('%d-%m-%Y')}"
        except Exception:
            pass

    try:
        trial_end = datetime.strptime(
            user["trial_end_date"], "%Y-%m-%d"
        ).date()

        if today <= trial_end:
            days = (trial_end - today).days
            return f"FREE TRIAL • {days} DAYS LEFT"
    except Exception:
        pass

    return "EXPIRED"


def generate_voucher_no(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"


def can_edit():
    return st.session_state.user_role == "Owner"


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.user_mobile:

    st.markdown("""
    <div class="main-header">
        <h1>🏢 SD TALLY BUSINESS</h1>
        <p>Professional Billing • GST • Inventory • Accounting</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🔐 Secure Login")

    mobile_input = st.text_input(
        "📱 Mobile Number",
        value=st.session_state.otp_mobile,
        max_chars=10,
        placeholder="Enter 10-digit mobile number"
    )

    if not st.session_state.otp_sent:

        if st.button("📨 SEND OTP", use_container_width=True):

            mobile_input = mobile_input.strip()

            if len(mobile_input) != 10 or not mobile_input.isdigit():
                st.error("Please enter a valid 10-digit mobile number.")
            else:
                otp = str(random.randint(1000, 9999))

                st.session_state.generated_otp = otp
                st.session_state.otp_mobile = mobile_input
                st.session_state.otp_sent = True

                st.success("OTP generated successfully.")
                st.info(
                    f"🔐 Testing OTP: {otp}"
                )

                st.rerun()

    else:

        st.success(
            f"OTP sent for mobile: {st.session_state.otp_mobile}"
        )

        otp_input = st.text_input(
            "🔐 Enter 4-Digit OTP",
            max_chars=4,
            type="password"
        )

        role = st.selectbox(
            "👨‍💼 Access Role",
            ["Owner", "Salesman / Staff"]
        )

        c1, c2 = st.columns(2)

        with c1:
            verify = st.button(
                "✅ VERIFY & LOGIN",
                use_container_width=True
            )

        with c2:
            resend = st.button(
                "🔄 RESEND OTP",
                use_container_width=True
            )

        if resend:
            otp = str(random.randint(1000, 9999))
            st.session_state.generated_otp = otp
            st.success("New OTP generated.")
            st.info(f"🔐 Testing OTP: {otp}")

        if verify:

            if otp_input != st.session_state.generated_otp:
                st.error("❌ Invalid OTP.")
            else:

                mobile = st.session_state.otp_mobile

                conn = get_db()

                existing = conn.execute(
                    "SELECT mobile FROM users WHERE mobile=?",
                    (mobile,)
                ).fetchone()

                if not existing:

                    trial_end = (
                        datetime.now().date()
                        + timedelta(days=10)
                    ).strftime("%Y-%m-%d")

                    conn.execute("""
                        INSERT INTO users
                        (mobile,name,reg_date,trial_end_date,is_paid,role)
                        VALUES (?,?,?,?,0,?)
                    """, (
                        mobile,
                        "Business User",
                        today_str(),
                        trial_end,
                        role
                    ))

                else:

                    # Owner is never accidentally changed by staff login
                    if role == "Owner":
                        conn.execute(
                            "UPDATE users SET role='Owner' WHERE mobile=?",
                            (mobile,)
                        )

                conn.commit()
                conn.close()

                st.session_state.user_mobile = mobile
                st.session_state.user_role = role
                st.session_state.otp_sent = False
                st.session_state.generated_otp = None

                refresh_user_session()

                st.rerun()

    st.stop()


# ============================================================
# RESTORE USER
# ============================================================

refresh_user_session()

mobile = st.session_state.user_mobile
status = subscription_status(mobile)


# ============================================================
# BUSINESS PROFILE SETUP
# ============================================================

if not st.session_state.business_name:

    st.markdown("""
    <div class="main-header">
        <h1>🏢 Business Profile Setup</h1>
        <p>Create your professional business workspace</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("business_setup"):

        name = st.text_input(
            "🏢 Business / Shop Name"
        )

        address = st.text_area(
            "📍 Business Address"
        )

        gstin = st.text_input(
            "🧾 GSTIN",
            placeholder="Optional"
        )

        save = st.form_submit_button(
            "💾 SAVE & OPEN WORKSPACE",
            use_container_width=True
        )

        if save:

            if not name.strip():
                st.error("Business Name is required.")
            else:

                conn = get_db()

                conn.execute("""
                    UPDATE users
                    SET business_name=?,
                        business_address=?,
                        gstin=?
                    WHERE mobile=?
                """, (
                    name.strip(),
                    address.strip(),
                    gstin.strip().upper(),
                    mobile
                ))

                conn.commit()
                conn.close()

                refresh_user_session()
                st.success("Business profile saved.")
                st.rerun()

    st.stop()


# ============================================================
# EXPIRED
# ============================================================

if status == "EXPIRED":

    st.markdown("""
    <div class="main-header">
        <h1>💳 Subscription Renewal</h1>
        <p>Your free trial has ended.</p>
    </div>
    """, unsafe_allow_html=True)

    st.warning(
        "Your subscription is expired. Please renew to continue."
    )

    st.markdown("### Renewal Amount")
    st.markdown("**₹112.10 including GST**")

    st.markdown(
        "**UPI ID:** `8381085702@ibl`"
    )

    msg = urllib.parse.quote(
        f"Hi, I have paid Rs.112.10 for SD Tally Business renewal. Mobile: {mobile}"
    )

    st.markdown(
        f"[📲 Send Payment Proof on WhatsApp](https://wa.me/918381085702?text={msg})"
    )

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.stop()


# ============================================================
# SIDEBAR PROFILE
# ============================================================

with st.sidebar:

    st.markdown("## 🏢 SD TALLY BUSINESS")

    st.markdown(f"""
    <div class="user-card">
        <div style="font-size:18px;font-weight:800;">
            👤 OWNER PROFILE
        </div>
        <hr>
        <b>📱 Mobile</b><br>
        {mobile}<br><br>

        <b>🏢 Business</b><br>
        {st.session_state.business_name}<br><br>

        <b>👨‍💼 Role</b><br>
        {st.session_state.user_role}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="plan-card">
        <b>🎁 PLAN</b><br>
        {status}
    </div>
    """, unsafe_allow_html=True)

    if st.button("✏️ Edit Business Profile", use_container_width=True):
        st.session_state["open_profile_edit"] = True
        st.rerun()

    if st.button("🚪 Logout Account", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")

    st.markdown("### 📌 Navigation")


# ============================================================
# PROFILE EDIT
# ============================================================

if st.session_state.get("open_profile_edit", False):

    st.markdown("""
    <div class="main-header">
        <h1>✏️ Edit Business Profile</h1>
        <p>Update your company information</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("edit_profile"):

        new_name = st.text_input(
            "🏢 Business Name",
            value=st.session_state.business_name
        )

        new_address = st.text_area(
            "📍 Business Address",
            value=st.session_state.business_address
        )

        new_gstin = st.text_input(
            "🧾 GSTIN",
            value=st.session_state.business_gstin
        )

        c1, c2 = st.columns(2)

        with c1:
            save_profile = st.form_submit_button(
                "💾 SAVE CHANGES",
                use_container_width=True
            )

        with c2:
            cancel_profile = st.form_submit_button(
                "✖ CANCEL",
                use_container_width=True
            )

        if save_profile:

            if not new_name.strip():
                st.error("Business name cannot be empty.")
            else:

                conn = get_db()

                conn.execute("""
                    UPDATE users
                    SET business_name=?,
                        business_address=?,
                        gstin=?
                    WHERE mobile=?
                """, (
                    new_name.strip(),
                    new_address.strip(),
                    new_gstin.strip().upper(),
                    mobile
                ))

                conn.commit()
                conn.close()

                st.session_state.open_profile_edit = False
                refresh_user_session()
                st.success("Profile updated successfully.")
                st.rerun()

        if cancel_profile:
            st.session_state.open_profile_edit = False
            st.rerun()


# ============================================================
# MENU
# ============================================================

menu_options = [
    "🏠 Dashboard",
    "📁 Masters",
    "🛒 Purchase Entry",
    "🧾 Tax Invoice / Sales",
    "📦 Barcode Quick Billing",
    "🔄 Sales Return / Purchase Return",
    "💰 Payment & Receipt",
    "🏦 Bank Accounts",
    "📊 Stock Summary & Ledger",
    "👥 Receivables & Payables",
    "📅 Day Book",
    "📒 Ledger & Trial Balance",
    "🔍 Voucher Search / Edit / Delete",
    "📈 Profit & Loss",
    "📋 Balance Sheet",
    "🧮 GST Reports",
    "🚚 e-Way / e-Invoice",
    "☁️ Backup & Export",
    "🏢 Branding & Signature",
    "👤 User & Permission",
    "⚙️ Company Settings"
]

menu = st.sidebar.selectbox(
    "Select Module",
    menu_options
)


# ============================================================
# HEADER
# ============================================================

st.markdown(f"""
<div class="main-header">
    <h1>{st.session_state.business_name}</h1>
    <p>
        SD TALLY BUSINESS Enterprise |
        {mobile} |
        {st.session_state.user_role}
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    conn = get_db()

    sales = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type IN ('Sales','Tax Invoice')
    """, (mobile,)).fetchone()[0]

    purchases = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
    """, (mobile,)).fetchone()[0]

    stock_value = conn.execute("""
        SELECT COALESCE(SUM(stock_qty * purchase_price),0)
        FROM inventory
        WHERE user_mobile=?
    """, (mobile,)).fetchone()[0]

    bank = conn.execute("""
        SELECT COALESCE(SUM(opening_balance),0)
        FROM bank_accounts
        WHERE user_mobile=?
    """, (mobile,)).fetchone()[0]

    conn.close()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Sales", money(sales))
    c2.metric("Purchase", money(purchases))
    c3.metric("Gross Profit", money(sales-purchases))
    c4.metric("Stock Value", money(stock_value))

    st.markdown("---")

    st.subheader("📊 Business Overview")

    chart = pd.DataFrame({
        "Category": [
            "Sales",
            "Purchase",
            "Gross Profit",
            "Stock"
        ],
        "Amount": [
            sales,
            purchases,
            sales-purchases,
            stock_value
        ]
    })

    st.bar_chart(
        chart.set_index("Category")
    )


# ============================================================
# MASTERS
# ============================================================

elif menu == "📁 Masters":

    st.subheader("⚙️ Masters Management")

    tab1, tab2, tab3 = st.tabs([
        "📦 Items",
        "🏢 Godowns",
        "👥 Parties"
    ])

    conn = get_db()

    # ---------------- ITEMS ----------------

    with tab1:

        st.markdown("### 📦 Item Master")

        with st.form("item_form"):

            item_name = st.text_input("Item Name")

            c1,c2 = st.columns(2)

            with c1:
                unit = st.selectbox(
                    "Unit",
                    ["PCS","KG","LTR","MTR","BOX","BAG","PACK","SQFT"]
                )

                sale_price = st.number_input(
                    "Sale Price",
                    min_value=0.0
                )

                purchase_price = st.number_input(
                    "Purchase Price",
                    min_value=0.0
                )

            with c2:

                gst_rate = st.selectbox(
                    "GST %",
                    [0.0,5.0,12.0,18.0,28.0]
                )

                stock_qty = st.number_input(
                    "Opening Stock",
                    min_value=0.0
                )

                barcode = st.text_input("Barcode")

            hsn = st.text_input("HSN / SAC")

            save_item = st.form_submit_button(
                "💾 SAVE ITEM",
                use_container_width=True
            )

            if save_item:

                if not item_name.strip():
                    st.error("Item name is required.")
                else:

                    conn.execute("""
                        INSERT INTO inventory
                        (
                            user_mobile,item_name,unit,
                            barcode,hsn_sac,
                            sale_price,purchase_price,
                            gst_rate,stock_qty
                        )
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (
                        mobile,
                        item_name.strip(),
                        unit,
                        barcode.strip(),
                        hsn.strip(),
                        sale_price,
                        purchase_price,
                        gst_rate,
                        stock_qty
                    ))

                    conn.commit()

                    st.success("Item saved successfully.")
                    st.rerun()

        st.markdown("---")

        items = pd.read_sql_query("""
            SELECT
                id,
                item_name AS Item,
                unit AS Unit,
                barcode AS Barcode,
                hsn_sac AS HSN,
                sale_price AS Sale,
                purchase_price AS Purchase,
                gst_rate AS GST,
                stock_qty AS Stock
            FROM inventory
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY id DESC
        """, conn, params=(mobile,))

        st.dataframe(
            items,
            use_container_width=True,
            hide_index=True
        )

        if not items.empty and can_edit():

            selected = st.selectbox(
                "Select Item",
                items["id"].tolist(),
                format_func=lambda x:
                    str(items.loc[items["id"] == x, "Item"].iloc[0])
            )

            c1,c2 = st.columns(2)

            with c1:
                if st.button("✏️ Edit Item", use_container_width=True):
                    st.session_state.edit_item_id = selected
                    st.rerun()

            with c2:
                if st.button("🗑️ Delete Item", use_container_width=True):

                    conn.execute("""
                        UPDATE inventory
                        SET is_active=0
                        WHERE id=? AND user_mobile=?
                    """, (selected,mobile))

                    conn.commit()

                    st.success("Item deleted.")
                    st.rerun()


    # ---------------- GODOWNS ----------------

    with tab2:

        st.markdown("### 🏢 Godown Master")

        with st.form("godown_form"):

            gname = st.text_input("Godown Name")
            gaddress = st.text_area("Godown Address")

            save_g = st.form_submit_button(
                "💾 SAVE GODOWN",
                use_container_width=True
            )

            if save_g:

                if not gname.strip():
                    st.error("Godown name required.")
                else:

                    conn.execute("""
                        INSERT INTO godowns
                        (user_mobile,godown_name,address)
                        VALUES (?,?,?)
                    """, (
                        mobile,
                        gname.strip(),
                        gaddress.strip()
                    ))

                    conn.commit()
                    st.success("Godown saved.")
                    st.rerun()

        godowns = pd.read_sql_query("""
            SELECT id,
                   godown_name AS Godown,
                   address AS Address
            FROM godowns
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY id DESC
        """, conn, params=(mobile,))

        st.dataframe(
            godowns,
            use_container_width=True,
            hide_index=True
        )

        if not godowns.empty and can_edit():

            gid = st.selectbox(
                "Select Godown",
                godowns["id"].tolist()
            )

            if st.button(
                "🗑️ Delete Godown",
                use_container_width=True
            ):

                conn.execute("""
                    UPDATE godowns
                    SET is_active=0
                    WHERE id=? AND user_mobile=?
                """,(gid,mobile))

                conn.commit()
                st.success("Godown deleted.")
                st.rerun()


    # ---------------- PARTIES ----------------

    with tab3:

        st.markdown("### 👥 Party Master")

        with st.form("party_form"):

            pname = st.text_input("Party Name")

            c1,c2 = st.columns(2)

            with c1:
                ptype = st.selectbox(
                    "Party Type",
                    ["Customer","Supplier"]
                )

                pmobile = st.text_input(
                    "Mobile Number"
                )

            with c2:
                pgstin = st.text_input(
                    "GSTIN"
                )

                opening = st.number_input(
                    "Opening Balance",
                    min_value=0.0
                )

            save_party = st.form_submit_button(
                "💾 SAVE PARTY",
                use_container_width=True
            )

            if save_party:

                if not pname.strip():
                    st.error("Party name required.")
                else:

                    conn.execute("""
                        INSERT INTO parties
                        (
                            user_mobile,party_name,
                            gstin,mobile,
                            party_type,opening_balance
                        )
                        VALUES (?,?,?,?,?,?)
                    """,(
                        mobile,
                        pname.strip(),
                        pgstin.strip().upper(),
                        pmobile.strip(),
                        ptype,
                        opening
                    ))

                    conn.commit()
                    st.success("Party saved.")
                    st.rerun()

        parties = pd.read_sql_query("""
            SELECT
                id,
                party_name AS Party,
                party_type AS Type,
                mobile AS Mobile,
                gstin AS GSTIN,
                opening_balance AS Opening
            FROM parties
            WHERE user_mobile=?
            AND is_active=1
            ORDER BY id DESC
        """, conn, params=(mobile,))

        st.dataframe(
            parties,
            use_container_width=True,
            hide_index=True
        )

        if not parties.empty and can_edit():

            pid = st.selectbox(
                "Select Party",
                parties["id"].tolist()
            )

            if st.button(
                "🗑️ Delete Party",
                use_container_width=True
            ):

                conn.execute("""
                    UPDATE parties
                    SET is_active=0
                    WHERE id=? AND user_mobile=?
                """,(pid,mobile))

                conn.commit()
                st.success("Party deleted.")
                st.rerun()

    conn.close()


# ============================================================
# SALES / TAX INVOICE
# ============================================================

elif menu == "🧾 Tax Invoice / Sales":

    st.subheader("🧾 Professional Tax Invoice")

    conn = get_db()

    invoice_no = st.text_input(
        "Invoice Number",
        value=generate_voucher_no("INV")
    )

    parties = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND party_type='Customer'
        AND is_active=1
        ORDER BY party_name
    """,conn,params=(mobile,))

    party_options = ["Walk-in Customer"] + parties["party_name"].tolist()

    party = st.selectbox(
        "Customer",
        party_options
    )

    items = pd.read_sql_query("""
        SELECT item_name,sale_price,gst_rate,stock_qty
        FROM inventory
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """,conn,params=(mobile,))

    if items.empty:
        st.warning("Please create Item Master first.")
    else:

        item = st.selectbox(
            "Item",
            items["item_name"].tolist()
        )

        row = items[items["item_name"] == item].iloc[0]

        qty = st.number_input(
            "Quantity",
            min_value=0.01,
            value=1.0
        )

        rate = st.number_input(
            "Rate",
            min_value=0.0,
            value=float(row["sale_price"])
        )

        gst = st.number_input(
            "GST %",
            min_value=0.0,
            max_value=28.0,
            value=float(row["gst_rate"])
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

        c1,c2,c3 = st.columns(3)

        c1.metric("Taxable",money(taxable))
        c2.metric("GST",money(gst_amount))
        c3.metric("Grand Total",money(total))

        if st.button(
            "💾 SAVE TAX INVOICE",
            use_container_width=True
        ):

            cgst = gst_amount / 2
            sgst = gst_amount / 2

            conn.execute("""
                INSERT INTO vouchers
                (
                    user_mobile,voucher_type,
                    voucher_no,date,
                    party_name,item_name,
                    unit,qty,rate,
                    taxable_amt,gst_rate,
                    cgst,sgst,igst,
                    total_amt,payment_mode
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(
                mobile,
                "Tax Invoice",
                invoice_no,
                today_str(),
                party,
                item,
                row.get("unit","PCS"),
                qty,
                rate,
                taxable,
                gst,
                cgst,
                sgst,
                0,
                total,
                payment_mode
            ))

            conn.execute("""
                UPDATE inventory
                SET stock_qty = stock_qty - ?
                WHERE user_mobile=?
                AND item_name=?
            """,(qty,mobile,item))

            conn.commit()

            st.success(
                f"Invoice {invoice_no} saved successfully."
            )

    conn.close()


# ============================================================
# PURCHASE
# ============================================================

elif menu == "🛒 Purchase Entry":

    st.subheader("🛒 Purchase Entry")

    conn = get_db()

    purchase_no = st.text_input(
        "Purchase Number",
        value=generate_voucher_no("PUR")
    )

    suppliers = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND party_type='Supplier'
        AND is_active=1
    """,conn,params=(mobile,))

    supplier_options = ["New / Cash Supplier"] + suppliers["party_name"].tolist()

    supplier = st.selectbox(
        "Supplier",
        supplier_options
    )

    items = pd.read_sql_query("""
        SELECT item_name,purchase_price,gst_rate
        FROM inventory
        WHERE user_mobile=?
        AND is_active=1
    """,conn,params=(mobile,))

    if items.empty:
        st.warning("Create Item Master first.")
    else:

        item = st.selectbox(
            "Item",
            items["item_name"].tolist()
        )

        row = items[items["item_name"] == item].iloc[0]

        qty = st.number_input(
            "Quantity",
            min_value=0.01,
            value=1.0
        )

        rate = st.number_input(
            "Purchase Rate",
            min_value=0.0,
            value=float(row["purchase_price"])
        )

        gst = st.number_input(
            "GST %",
            min_value=0.0,
            max_value=28.0,
            value=float(row["gst_rate"])
        )

        payment = st.selectbox(
            "Payment Mode",
            ["Cash","Bank / UPI","Credit"]
        )

        taxable = qty * rate
        gst_amt = taxable * gst / 100
        total = taxable + gst_amt

        st.metric(
            "Purchase Total",
            money(total)
        )

        if st.button(
            "💾 SAVE PURCHASE",
            use_container_width=True
        ):

            conn.execute("""
                INSERT INTO vouchers
                (
                    user_mobile,voucher_type,
                    voucher_no,date,
                    party_name,item_name,
                    qty,rate,taxable_amt,
                    gst_rate,cgst,sgst,
                    total_amt,payment_mode
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(
                mobile,
                "Purchase",
                purchase_no,
                today_str(),
                supplier,
                item,
                qty,
                rate,
                taxable,
                gst,
                gst_amt/2,
                gst_amt/2,
                total,
                payment
            ))

            conn.execute("""
                UPDATE inventory
                SET stock_qty=stock_qty+?,
                    purchase_price=?
                WHERE user_mobile=?
                AND item_name=?
            """,(qty,rate,mobile,item))

            conn.commit()

            st.success("Purchase saved successfully.")

    conn.close()


# ============================================================
# BARCODE BILLING
# ============================================================

elif menu == "📦 Barcode Quick Billing":

    st.subheader("📦 Barcode Quick Billing")

    conn = get_db()

    barcode = st.text_input(
        "Scan / Enter Barcode"
    )

    if barcode:

        row = conn.execute("""
            SELECT *
            FROM inventory
            WHERE user_mobile=?
            AND barcode=?
            AND is_active=1
        """,(mobile,barcode)).fetchone()

        if row:

            st.success(
                f"Item Found: {row['item_name']}"
            )

            qty = st.number_input(
                "Quantity",
                min_value=1.0,
                value=1.0
            )

            amount = qty * row["sale_price"]

            st.metric(
                "Bill Amount",
                money(amount)
            )

            if st.button(
                "💾 CREATE QUICK BILL",
                use_container_width=True
            ):

                conn.execute("""
                    INSERT INTO vouchers
                    (
                        user_mobile,voucher_type,
                        voucher_no,date,
                        item_name,qty,rate,
                        taxable_amt,total_amt,
                        payment_mode
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """,(
                    mobile,
                    "Sales",
                    generate_voucher_no("POS"),
                    today_str(),
                    row["item_name"],
                    qty,
                    row["sale_price"],
                    amount,
                    amount,
                    "Cash"
                ))

                conn.execute("""
                    UPDATE inventory
                    SET stock_qty=stock_qty-?
                    WHERE id=?
                """,(qty,row["id"]))

                conn.commit()

                st.success("Quick bill created.")

        else:
            st.error("Barcode not found.")

    conn.close()


# ============================================================
# PAYMENT & RECEIPT
# ============================================================

elif menu == "💰 Payment & Receipt":

    st.subheader("💰 Payment & Receipt Management")

    with st.form("payment_form"):

        ptype = st.selectbox(
            "Type",
            ["Payment","Receipt"]
        )

        party = st.text_input(
            "Party Name"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        mode = st.selectbox(
            "Mode",
            ["Cash","Bank / UPI","Cheque"]
        )

        narration = st.text_input(
            "Narration"
        )

        save = st.form_submit_button(
            "💾 SAVE TRANSACTION",
            use_container_width=True
        )

        if save:

            if amount <= 0:
                st.error("Enter valid amount.")
            else:

                conn = get_db()

                conn.execute("""
                    INSERT INTO payments
                    (
                        user_mobile,date,
                        payment_type,party_name,
                        amount,mode,narration
                    )
                    VALUES (?,?,?,?,?,?,?)
                """,(
                    mobile,
                    today_str(),
                    ptype,
                    party,
                    amount,
                    mode,
                    narration
                ))

                conn.commit()
                conn.close()

                st.success("Transaction saved.")
                st.rerun()

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            id,date,
            payment_type AS Type,
            party_name AS Party,
            amount AS Amount,
            mode AS Mode,
            narration AS Narration
        FROM payments
        WHERE user_mobile=?
        ORDER BY id DESC
    """,conn,params=(mobile,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    conn.close()


# ============================================================
# BANK
# ============================================================

elif menu == "🏦 Bank Accounts":

    st.subheader("🏦 Bank Account Management")

    conn = get_db()

    with st.form("bank_form"):

        bank_name = st.text_input("Bank Name")
        account = st.text_input("Account Number")
        ifsc = st.text_input("IFSC Code")
        branch = st.text_input("Branch")
        opening = st.number_input(
            "Opening Balance",
            min_value=0.0
        )

        save = st.form_submit_button(
            "💾 SAVE BANK ACCOUNT",
            use_container_width=True
        )

        if save:

            if not bank_name.strip():
                st.error("Bank name required.")
            else:

                conn.execute("""
                    INSERT INTO bank_accounts
                    (
                        user_mobile,bank_name,
                        account_no,ifsc_code,
                        branch_name,opening_balance
                    )
                    VALUES (?,?,?,?,?,?)
                """,(
                    mobile,
                    bank_name,
                    account,
                    ifsc.upper(),
                    branch,
                    opening
                ))

                conn.commit()
                st.success("Bank account saved.")
                st.rerun()

    banks = pd.read_sql_query("""
        SELECT
            id,
            bank_name AS Bank,
            account_no AS Account,
            ifsc_code AS IFSC,
            branch_name AS Branch,
            opening_balance AS Opening
        FROM bank_accounts
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY id DESC
    """,conn,params=(mobile,))

    st.dataframe(
        banks,
        use_container_width=True,
        hide_index=True
    )

    if not banks.empty and can_edit():

        bid = st.selectbox(
            "Select Bank Account",
            banks["id"].tolist()
        )

        if st.button(
            "🗑️ DELETE BANK ACCOUNT",
            use_container_width=True
        ):

            conn.execute("""
                UPDATE bank_accounts
                SET is_active=0
                WHERE id=? AND user_mobile=?
            """,(bid,mobile))

            conn.commit()
            st.success("Bank account deleted.")
            st.rerun()

    conn.close()


# ============================================================
# STOCK
# ============================================================

elif menu == "📊 Stock Summary & Ledger":

    st.subheader("📊 Stock Summary")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            stock_qty AS Quantity,
            purchase_price AS Purchase,
            sale_price AS Sale,
            gst_rate AS GST,
            (stock_qty*purchase_price) AS Stock_Value
        FROM inventory
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """,conn,params=(mobile,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:
        st.metric(
            "Total Stock Value",
            money(df["Stock_Value"].sum())
        )

    conn.close()


# ============================================================
# DAY BOOK
# ============================================================

elif menu == "📅 Day Book":

    st.subheader("📅 Day Book")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Type,
            voucher_no AS Voucher,
            party_name AS Party,
            total_amt AS Amount,
            payment_mode AS Mode
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY date DESC,id DESC
    """,conn,params=(mobile,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    conn.close()


# ============================================================
# VOUCHER SEARCH / DELETE
# ============================================================

elif menu == "🔍 Voucher Search / Edit / Delete":

    st.subheader("🔍 Voucher Register")

    conn = get_db()

    search = st.text_input(
        "Search Voucher / Party / Item"
    )

    df = pd.read_sql_query("""
        SELECT
            id,
            voucher_type AS Type,
            voucher_no AS Voucher,
            date AS Date,
            party_name AS Party,
            item_name AS Item,
            qty AS Qty,
            total_amt AS Amount,
            payment_mode AS Mode
        FROM vouchers
        WHERE user_mobile=?
        ORDER BY id DESC
    """,conn,params=(mobile,))

    if search.strip():

        mask = (
            df.astype(str)
            .apply(
                lambda col: col.str.contains(
                    search,
                    case=False,
                    na=False
                )
            )
            .any(axis=1)
        )

        df = df[mask]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty and can_edit():

        vid = st.selectbox(
            "Select Voucher ID",
            df["id"].tolist()
        )

        c1,c2 = st.columns(2)

        with c1:

            if st.button(
                "🗑️ DELETE VOUCHER",
                use_container_width=True
            ):

                conn.execute("""
                    DELETE FROM vouchers
                    WHERE id=? AND user_mobile=?
                """,(vid,mobile))

                conn.commit()

                st.success("Voucher deleted.")
                st.rerun()

        with c2:

            if st.button(
                "✏️ EDIT AMOUNT",
                use_container_width=True
            ):

                st.session_state.edit_voucher_id = vid
                st.rerun()

        if st.session_state.edit_voucher_id == vid:

            current = conn.execute("""
                SELECT total_amt
                FROM vouchers
                WHERE id=? AND user_mobile=?
            """,(vid,mobile)).fetchone()

            if current:

                new_amount = st.number_input(
                    "New Total Amount",
                    min_value=0.0,
                    value=float(current["total_amt"])
                )

                if st.button(
                    "💾 SAVE EDIT",
                    use_container_width=True
                ):

                    conn.execute("""
                        UPDATE vouchers
                        SET total_amt=?
                        WHERE id=? AND user_mobile=?
                    """,(
                        new_amount,
                        vid,
                        mobile
                    ))

                    conn.commit()

                    st.session_state.edit_voucher_id = None

                    st.success("Voucher updated.")
                    st.rerun()

    conn.close()


# ============================================================
# RECEIVABLES
# ============================================================

elif menu == "👥 Receivables & Payables":

    st.subheader("👥 Receivables & Payables")

    conn = get_db()

    c1,c2 = st.columns(2)

    with c1:

        st.markdown("### 🟢 Customer Receivables")

        receivable = pd.read_sql_query("""
            SELECT
                party_name AS Customer,
                SUM(total_amt) AS Outstanding
            FROM vouchers
            WHERE user_mobile=?
            AND voucher_type IN ('Sales','Tax Invoice')
            AND payment_mode='Credit (Pending)'
            GROUP BY party_name
        """,conn,params=(mobile,))

        st.dataframe(
            receivable,
            use_container_width=True,
            hide_index=True
        )

    with c2:

        st.markdown("### 🔴 Supplier Payables")

        payable = pd.read_sql_query("""
            SELECT
                party_name AS Supplier,
                SUM(total_amt) AS Outstanding
            FROM vouchers
            WHERE user_mobile=?
            AND voucher_type='Purchase'
            AND payment_mode='Credit'
            GROUP BY party_name
        """,conn,params=(mobile,))

        st.dataframe(
            payable,
            use_container_width=True,
            hide_index=True
        )

    conn.close()


# ============================================================
# LEDGER
# ============================================================

elif menu == "📒 Ledger & Trial Balance":

    st.subheader("📒 Ledger & Trial Balance")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            party_name AS Party,
            voucher_type AS Type,
            COUNT(*) AS Entries,
            SUM(total_amt) AS Total
        FROM vouchers
        WHERE user_mobile=?
        GROUP BY party_name,voucher_type
        ORDER BY Party
    """,conn,params=(mobile,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    conn.close()


# ============================================================
# PROFIT & LOSS
# ============================================================

elif menu == "📈 Profit & Loss":

    st.subheader("📈 Profit & Loss Account")

    conn = get_db()

    sales = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type IN ('Sales','Tax Invoice')
    """,(mobile,)).fetchone()[0]

    purchases = conn.execute("""
        SELECT COALESCE(SUM(total_amt),0)
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type='Purchase'
    """,(mobile,)).fetchone()[0]

    profit = sales - purchases

    c1,c2,c3 = st.columns(3)

    c1.metric("Sales",money(sales))
    c2.metric("Purchase",money(purchases))
    c3.metric("Gross Profit",money(profit))

    conn.close()


# ============================================================
# BALANCE SHEET
# ============================================================

elif menu == "📋 Balance Sheet":

    st.subheader("📋 Balance Sheet Summary")

    conn = get_db()

    stock = conn.execute("""
        SELECT COALESCE(SUM(stock_qty*purchase_price),0)
        FROM inventory
        WHERE user_mobile=?
    """,(mobile,)).fetchone()[0]

    bank = conn.execute("""
        SELECT COALESCE(SUM(opening_balance),0)
        FROM bank_accounts
        WHERE user_mobile=?
    """,(mobile,)).fetchone()[0]

    capital = conn.execute("""
        SELECT COALESCE(SUM(opening_balance),0)
        FROM parties
        WHERE user_mobile=?
    """,(mobile,)).fetchone()[0]

    df = pd.DataFrame({
        "Particulars":[
            "Stock",
            "Bank Balance",
            "Party Opening Balance"
        ],
        "Amount":[
            stock,
            bank,
            capital
        ]
    })

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    conn.close()


# ============================================================
# GST REPORT
# ============================================================

elif menu == "🧮 GST Reports":

    st.subheader("🧮 GST Reports")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Invoice,
            party_name AS Party,
            taxable_amt AS Taxable,
            gst_rate AS GST_Rate,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amt AS Total
        FROM vouchers
        WHERE user_mobile=?
        AND voucher_type IN ('Sales','Tax Invoice')
        ORDER BY date DESC
    """,conn,params=(mobile,))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:

        st.markdown("### GST Summary")

        summary = pd.DataFrame({
            "Taxable": [df["Taxable"].sum()],
            "CGST": [df["CGST"].sum()],
            "SGST": [df["SGST"].sum()],
            "IGST": [df["IGST"].sum()],
            "Total": [df["Total"].sum()]
        })

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )

    conn.close()


# ============================================================
# RETURNS
# ============================================================

elif menu == "🔄 Sales Return / Purchase Return":

    st.subheader("🔄 Sales / Purchase Return")

    conn = get_db()

    return_type = st.selectbox(
        "Return Type",
        ["Sales Return","Purchase Return"]
    )

    party = st.text_input("Party Name")
    item = st.text_input("Item Name")
    qty = st.number_input(
        "Quantity",
        min_value=0.01,
        value=1.0
    )

    rate = st.number_input(
        "Rate",
        min_value=0.0
    )

    if st.button(
        "💾 SAVE RETURN",
        use_container_width=True
    ):

        total = qty * rate

        conn.execute("""
            INSERT INTO vouchers
            (
                user_mobile,voucher_type,
                voucher_no,date,
                party_name,item_name,
                qty,rate,total_amt,
                payment_mode
            )
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """,(
            mobile,
            return_type,
            generate_voucher_no("RET"),
            today_str(),
            party,
            item,
            qty,
            rate,
            total,
            "Adjustment"
        ))

        conn.commit()

        st.success("Return saved successfully.")

    conn.close()


# ============================================================
# E-WAY / E-INVOICE
# ============================================================

elif menu == "🚚 e-Way / e-Invoice":

    st.subheader("🚚 e-Way Bill & e-Invoice")

    st.info(
        "Enter official portal reference details here. "
        "Actual government portal submission requires official API credentials."
    )

    eway = st.text_input("e-Way Bill Number")
    irn = st.text_input("IRN Number")

    st.text_area(
        "Notes"
    )

    st.button(
        "💾 SAVE PORTAL DETAILS",
        use_container_width=True
    )


# ============================================================
# BACKUP / EXPORT
# ============================================================

elif menu == "☁️ Backup & Export":

    st.subheader("☁️ Backup & Report Export")

    conn = get_db()

    tables = [
        "users",
        "inventory",
        "godowns",
        "parties",
        "bank_accounts",
        "vouchers",
        "payments",
        "bank_transactions"
    ]

    for table in tables:

        df = pd.read_sql_query(
            f"SELECT * FROM {table} WHERE user_mobile=?",
            conn,
            params=(mobile,)
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            f"⬇️ Download {table.upper()}",
            csv,
            file_name=f"{table}_backup.csv",
            mime="text/csv",
            use_container_width=True
        )

    conn.close()


# ============================================================
# BRANDING
# ============================================================

elif menu == "🏢 Branding & Signature":

    st.subheader("🏢 Company Branding & Signature")

    logo = st.file_uploader(
        "Upload Company Logo",
        type=["png","jpg","jpeg"]
    )

    signature = st.file_uploader(
        "Upload Signature",
        type=["png","jpg","jpeg"]
    )

    if st.button(
        "💾 SAVE BRANDING",
        use_container_width=True
    ):

        import base64

        logo_b64 = ""
        sig_b64 = ""

        if logo:
            logo_b64 = base64.b64encode(
                logo.getvalue()
            ).decode()

        if signature:
            sig_b64 = base64.b64encode(
                signature.getvalue()
            ).decode()

        conn = get_db()

        conn.execute("""
            INSERT INTO branding
            (user_mobile,logo_base64,signature_base64)
            VALUES (?,?,?)
            ON CONFLICT(user_mobile)
            DO UPDATE SET
                logo_base64=excluded.logo_base64,
                signature_base64=excluded.signature_base64
        """,(
            mobile,
            logo_b64,
            sig_b64
        ))

        conn.commit()
        conn.close()

        st.success("Branding saved successfully.")


# ============================================================
# USER / PERMISSION
# ============================================================

elif menu == "👤 User & Permission":

    st.subheader("👤 User & Permission Management")

    user = load_user(mobile)

    st.markdown(f"""
    <div class="profile-card">
        <b>Mobile:</b> {mobile}<br>
        <b>Business:</b> {st.session_state.business_name}<br>
        <b>Current Role:</b> {user["role"]}
    </div>
    """,unsafe_allow_html=True)

    if can_edit():

        new_role = st.selectbox(
            "Default Access Role",
            ["Owner","Salesman / Staff"],
            index=0 if user["role"]=="Owner" else 1
        )

        if st.button(
            "💾 SAVE PERMISSION",
            use_container_width=True
        ):

            conn = get_db()

            conn.execute("""
                UPDATE users
                SET role=?
                WHERE mobile=?
            """,(new_role,mobile))

            conn.commit()
            conn.close()

            refresh_user_session()

            st.success("Permission updated.")
            st.rerun()

    else:
        st.info(
            "Only Owner can modify permissions."
        )


# ============================================================
# COMPANY SETTINGS
# ============================================================

elif menu == "⚙️ Company Settings":

    st.subheader("⚙️ Company Settings")

    st.write(
        f"**Business Name:** {st.session_state.business_name}"
    )

    st.write(
        f"**Address:** {st.session_state.business_address}"
    )

    st.write(
        f"**GSTIN:** {st.session_state.business_gstin or 'Not Added'}"
    )

    st.write(
        f"**Mobile:** {mobile}"
    )

    st.write(
        f"**Role:** {st.session_state.user_role}"
    )

    st.info(
        "Use 'Edit Business Profile' from the sidebar "
        "to update company information."
    )


# ============================================================
# DEFAULT / PRINT
# ============================================================

else:

    st.info(
        "Select a module from the Navigation menu."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "© SD TALLY BUSINESS • Professional Business Management System"
)
