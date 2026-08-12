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
# ============================================================
# SD TALLY BUSINESS ENTERPRISE
# STEP 2 — CORE ACCOUNTING ENGINE
# ============================================================

# ============================================================
# COMMON DATABASE HELPERS
# ============================================================

def execute_query(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def fetch_one(query, params=()):
    conn = get_db()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row


def fetch_all(query, params=()):
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_next_voucher_no(voucher_type):
    mob = st.session_state.user_mobile

    row = fetch_one("""
        SELECT COUNT(*)
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type=?
    """, (mob, voucher_type))

    number = (row[0] if row else 0) + 1

    prefix = {
        "Sales": "SAL",
        "Purchase": "PUR",
        "Receipt": "REC",
        "Payment": "PAY",
        "Contra": "CON",
        "Journal": "JRN",
        "Sales Return": "SR",
        "Purchase Return": "PR"
    }.get(voucher_type, "VCH")

    return f"{prefix}-{number:05d}"


def calculate_gst(taxable, gst_rate, same_state=True):

    gst_amount = float(taxable) * float(gst_rate) / 100

    if same_state:
        cgst = gst_amount / 2
        sgst = gst_amount / 2
        igst = 0
    else:
        cgst = 0
        sgst = 0
        igst = gst_amount

    return round(cgst, 2), round(sgst, 2), round(igst, 2)


def post_ledger(
    account_name,
    account_type,
    voucher_type,
    voucher_no,
    particulars,
    debit=0,
    credit=0
):

    mob = st.session_state.user_mobile

    previous = fetch_one("""
        SELECT COALESCE(SUM(debit-credit),0)
        FROM ledger
        WHERE user_mobile=?
        AND account_name=?
    """, (mob, account_name))

    old_balance = float(previous[0]) if previous else 0
    balance = old_balance + float(debit) - float(credit)

    execute_query("""
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
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        mob,
        today(),
        account_name,
        account_type,
        voucher_type,
        voucher_no,
        particulars,
        debit,
        credit,
        balance,
        now()
    ))


def update_stock(item_name, qty, movement_type, rate=0, reference_no=""):

    mob = st.session_state.user_mobile

    item = fetch_one("""
        SELECT id, current_stock, godown, unit
        FROM items
        WHERE user_mobile=?
        AND item_name=?
        AND is_active=1
        LIMIT 1
    """, (mob, item_name))

    if not item:
        return False, "Item not found."

    item_id = item[0]
    current_stock = float(item[1] or 0)
    godown = item[2] or "Main Store"

    qty = float(qty)

    if movement_type in ["SALE", "PURCHASE_RETURN"]:

        if current_stock < qty:
            return False, f"Insufficient stock. Available: {current_stock}"

        new_stock = current_stock - qty
        qty_in = 0
        qty_out = qty

    else:

        new_stock = current_stock + qty
        qty_in = qty
        qty_out = 0

    execute_query("""
        UPDATE items
        SET current_stock=?
        WHERE id=?
    """, (new_stock, item_id))

    execute_query("""
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
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        mob,
        today(),
        item_name,
        godown,
        movement_type,
        reference_no,
        qty_in,
        qty_out,
        new_stock,
        rate,
        now()
    ))

    return True, new_stock


def save_transaction(
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
    round_off,
    total_amount,
    payment_mode="",
    debit_account="",
    credit_account="",
    narration=""
):

    mob = st.session_state.user_mobile

    execute_query("""
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
            round_off,
            total_amount,
            payment_mode,
            debit_account,
            credit_account,
            narration,
            created_at
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        mob,
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
        round_off,
        total_amount,
        payment_mode,
        debit_account,
        credit_account,
        narration,
        now()
    ))


# ============================================================
# VOUCHER MENU
# ============================================================

elif menu == "🧾 Vouchers":

    st.subheader("🧾 Accounting Vouchers")

    voucher_tab = st.tabs([
        "🛒 Sales",
        "📥 Purchase",
        "💵 Receipt",
        "💸 Payment",
        "🔄 Contra",
        "📘 Journal",
        "↩️ Sales Return",
        "↩️ Purchase Return"
    ])

    # ========================================================
    # SALES
    # ========================================================

    with voucher_tab[0]:

        st.subheader("🛒 Sales Invoice")

        voucher_no = get_next_voucher_no("Sales")

        st.info(f"Voucher No: {voucher_no}")

        with st.form("sales_voucher_form"):

            c1, c2 = st.columns(2)

            sale_date = c1.date_input(
                "Invoice Date",
                value=datetime.now().date()
            )

            party_rows = fetch_all("""
                SELECT party_name
                FROM parties
                WHERE user_mobile=?
                AND is_active=1
                ORDER BY party_name
            """, (mob,))

            party_list = ["Cash Customer"] + [
                r[0] for r in party_rows
            ]

            party = c2.selectbox(
                "Customer",
                party_list
            )

            item_rows = fetch_all("""
                SELECT item_name
                FROM items
                WHERE user_mobile=?
                AND is_active=1
                ORDER BY item_name
            """, (mob,))

            item_list = [r[0] for r in item_rows]

            if item_list:

                item = st.selectbox(
                    "Item",
                    item_list
                )

                item_data = fetch_one("""
                    SELECT
                        unit,
                        hsn_sac,
                        gst_rate,
                        sale_price,
                        current_stock
                    FROM items
                    WHERE user_mobile=?
                    AND item_name=?
                    AND is_active=1
                    LIMIT 1
                """, (mob, item))

                item_unit = item_data[0]
                item_hsn = item_data[1]
                item_gst = float(item_data[2] or 0)
                default_rate = float(item_data[3] or 0)
                available_stock = float(item_data[4] or 0)

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

                st.caption(
                    f"Available Stock: {available_stock} {item_unit}"
                )

                gst_rate = st.number_input(
                    "GST %",
                    min_value=0.0,
                    max_value=100.0,
                    value=item_gst
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

                taxable = max(
                    0,
                    (qty * rate) - discount
                )

                cgst, sgst, igst = calculate_gst(
                    taxable,
                    gst_rate,
                    same_state=True
                )

                total = round(
                    taxable + cgst + sgst + igst,
                    2
                )

                st.markdown(
                    f"""
                    **Taxable Amount:** {money(taxable)}  
                    **CGST:** {money(cgst)}  
                    **SGST:** {money(sgst)}  
                    **IGST:** {money(igst)}  
                    **Grand Total:** {money(total)}
                    """
                )

                save_sales = st.form_submit_button(
                    "💾 SAVE SALES INVOICE"
                )

                if save_sales:

                    if qty <= 0:
                        st.error("Quantity must be greater than zero.")

                    elif rate < 0:
                        st.error("Invalid rate.")

                    elif qty > available_stock:
                        st.error(
                            f"Insufficient stock. Available stock: {available_stock}"
                        )

                    else:

                        ok, result = update_stock(
                            item,
                            qty,
                            "SALE",
                            rate,
                            voucher_no
                        )

                        if ok:

                            save_transaction(
                                "Sales",
                                voucher_no,
                                str(sale_date),
                                party,
                                item,
                                item_unit,
                                item_hsn,
                                qty,
                                rate,
                                discount,
                                taxable,
                                gst_rate,
                                cgst,
                                sgst,
                                igst,
                                0,
                                total,
                                payment_mode,
                                "Sales Account",
                                payment_mode,
                                narration
                            )

                            post_ledger(
                                party,
                                "Customer",
                                "Sales",
                                voucher_no,
                                f"Sales - {item}",
                                total,
                                0
                            )

                            post_ledger(
                                "Sales Account",
                                "Income",
                                "Sales",
                                voucher_no,
                                f"Sales - {item}",
                                0,
                                taxable
                            )

                            if cgst > 0:
                                post_ledger(
                                    "Output CGST",
                                    "GST",
                                    "Sales",
                                    voucher_no,
                                    "CGST",
                                    0,
                                    cgst
                                )

                            if sgst > 0:
                                post_ledger(
                                    "Output SGST",
                                    "GST",
                                    "Sales",
                                    voucher_no,
                                    "SGST",
                                    0,
                                    sgst
                                )

                            log_action(
                                "Sales Invoice Created",
                                "Sales",
                                voucher_no
                            )

                            st.success(
                                f"✅ Sales Invoice {voucher_no} saved successfully."
                            )

                        else:

                            st.error(str(result))

            else:

                st.warning(
                    "No items available. Please create an item first from Masters."
                )


    # ========================================================
    # PURCHASE
    # ========================================================

    with voucher_tab[1]:

        st.subheader("📥 Purchase Invoice")

        voucher_no = get_next_voucher_no("Purchase")

        st.info(f"Voucher No: {voucher_no}")

        with st.form("purchase_voucher_form"):

            c1, c2 = st.columns(2)

            purchase_date = c1.date_input(
                "Purchase Date",
                value=datetime.now().date()
            )

            supplier_rows = fetch_all("""
                SELECT party_name
                FROM parties
                WHERE user_mobile=?
                AND is_active=1
                AND party_type IN ('Supplier','Both')
                ORDER BY party_name
            """, (mob,))

            supplier_list = ["Cash Supplier"] + [
                r[0] for r in supplier_rows
            ]

            supplier = c2.selectbox(
                "Supplier",
                supplier_list
            )

            item_rows = fetch_all("""
                SELECT item_name
                FROM items
                WHERE user_mobile=?
                AND is_active=1
                ORDER BY item_name
            """, (mob,))

            item_list = [r[0] for r in item_rows]

            if item_list:

                item = st.selectbox(
                    "Item",
                    item_list,
                    key="purchase_item"
                )

                item_data = fetch_one("""
                    SELECT
                        unit,
                        hsn_sac,
                        gst_rate,
                        purchase_price
                    FROM items
                    WHERE user_mobile=?
                    AND item_name=?
                    AND is_active=1
                    LIMIT 1
                """, (mob, item))

                item_unit = item_data[0]
                item_hsn = item_data[1]
                item_gst = float(item_data[2] or 0)
                default_rate = float(item_data[3] or 0)

                c1, c2, c3 = st.columns(3)

                qty = c1.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=1.0,
                    key="purchase_qty"
                )

                rate = c2.number_input(
                    "Purchase Rate",
                    min_value=0.0,
                    value=default_rate,
                    key="purchase_rate"
                )

                discount = c3.number_input(
                    "Discount",
                    min_value=0.0,
                    value=0.0,
                    key="purchase_discount"
                )

                gst_rate = st.number_input(
                    "GST %",
                    min_value=0.0,
                    max_value=100.0,
                    value=item_gst,
                    key="purchase_gst"
                )

                payment_mode = st.selectbox(
                    "Payment Mode",
                    [
                        "Credit",
                        "Cash",
                        "Bank",
                        "UPI"
                    ],
                    key="purchase_payment"
                )

                narration = st.text_area(
                    "Narration",
                    key="purchase_narration"
                )

                taxable = max(
                    0,
                    (qty * rate) - discount
                )

                cgst, sgst, igst = calculate_gst(
                    taxable,
                    gst_rate,
                    same_state=True
                )

                total = round(
                    taxable + cgst + sgst + igst,
                    2
                )

                st.markdown(
                    f"""
                    **Taxable Amount:** {money(taxable)}  
                    **CGST:** {money(cgst)}  
                    **SGST:** {money(sgst)}  
                    **Grand Total:** {money(total)}
                    """
                )

                save_purchase = st.form_submit_button(
                    "💾 SAVE PURCHASE"
                )

                if save_purchase:

                    if qty <= 0:

                        st.error(
                            "Quantity must be greater than zero."
                        )

                    else:

                        ok, result = update_stock(
                            item,
                            qty,
                            "PURCHASE",
                            rate,
                            voucher_no
                        )

                        if ok:

                            save_transaction(
                                "Purchase",
                                voucher_no,
                                str(purchase_date),
                                supplier,
                                item,
                                item_unit,
                                item_hsn,
                                qty,
                                rate,
                                discount,
                                taxable,
                                gst_rate,
                                cgst,
                                sgst,
                                igst,
                                0,
                                total,
                                payment_mode,
                                "Purchase Account",
                                payment_mode,
                                narration
                            )

                            post_ledger(
                                "Purchase Account",
                                "Expense",
                                "Purchase",
                                voucher_no,
                                f"Purchase - {item}",
                                taxable,
                                0
                            )

                            post_ledger(
                                supplier,
                                "Supplier",
                                "Purchase",
                                voucher_no,
                                f"Purchase - {item}",
                                0,
                                total
                            )

                            log_action(
                                "Purchase Invoice Created",
                                "Purchase",
                                voucher_no
                            )

                            st.success(
                                f"✅ Purchase {voucher_no} saved successfully."
                            )

                        else:

                            st.error(str(result))

            else:

                st.warning(
                    "No items available. Please create an item first."
                )


    # ========================================================
    # RECEIPT
    # ========================================================

    with voucher_tab[2]:

        st.subheader("💵 Receipt Voucher")

        voucher_no = get_next_voucher_no("Receipt")

        with st.form("receipt_form"):

            receipt_date = st.date_input(
                "Date",
                value=datetime.now().date(),
                key="receipt_date"
            )

            party_rows = fetch_all("""
                SELECT party_name
                FROM parties
                WHERE user_mobile=?
                AND is_active=1
                ORDER BY party_name
            """, (mob,))

            party_list = [
                r[0] for r in party_rows
            ]

            party_list = (
                party_list
                if party_list
                else ["Cash / Other"]
            )

            party = st.selectbox(
                "Received From",
                party_list,
                key="receipt_party"
            )

            amount = st.number_input(
                "Amount Received",
                min_value=0.0,
                key="receipt_amount"
            )

            mode = st.selectbox(
                "Received Through",
                [
                    "Cash",
                    "Bank",
                    "UPI"
                ],
                key="receipt_mode"
            )

            narration = st.text_area(
                "Narration",
                key="receipt_narration"
            )

            save_receipt = st.form_submit_button(
                "💾 SAVE RECEIPT"
            )

            if save_receipt and amount > 0:

                save_transaction(
                    "Receipt",
                    voucher_no,
                    str(receipt_date),
                    party,
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
                    0,
                    amount,
                    mode,
                    mode,
                    party,
                    narration
                )

                post_ledger(
                    mode,
                    "Cash/Bank",
                    "Receipt",
                    voucher_no,
                    narration or "Receipt",
                    amount,
                    0
                )

                post_ledger(
                    party,
                    "Customer",
                    "Receipt",
                    voucher_no,
                    narration or "Receipt",
                    0,
                    amount
                )

                log_action(
                    "Receipt Created",
                    "Receipt",
                    voucher_no
                )

                st.success(
                    f"✅ Receipt {voucher_no} saved."
                )

            elif save_receipt:

                st.error(
                    "Amount must be greater than zero."
                )


    # ========================================================
    # PAYMENT
    # ========================================================

    with voucher_tab[3]:

        st.subheader("💸 Payment Voucher")

        voucher_no = get_next_voucher_no("Payment")

        with st.form("payment_form"):

            payment_date = st.date_input(
                "Date",
                value=datetime.now().date(),
                key="payment_date"
            )

            supplier_rows = fetch_all("""
                SELECT party_name
                FROM parties
                WHERE user_mobile=?
                AND is_active=1
                ORDER BY party_name
            """, (mob,))

            supplier_list = [
                r[0] for r in supplier_rows
            ]

            supplier_list = (
                supplier_list
                if supplier_list
                else ["Cash / Other"]
            )

            paid_to = st.selectbox(
                "Paid To",
                supplier_list,
                key="payment_party"
            )

            amount = st.number_input(
                "Amount Paid",
                min_value=0.0,
                key="payment_amount"
            )

            mode = st.selectbox(
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

            if save_payment and amount > 0:

                save_transaction(
                    "Payment",
                    voucher_no,
                    str(payment_date),
                    paid_to,
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
                    0,
                    amount,
                    mode,
                    paid_to,
                    mode,
                    narration
                )

                post_ledger(
                    paid_to,
                    "Supplier",
                    "Payment",
                    voucher_no,
                    narration or "Payment",
                    amount,
                    0
                )

                post_ledger(
                    mode,
                    "Cash/Bank",
                    "Payment",
                    voucher_no,
                    narration or "Payment",
                    0,
                    amount
                )

                log_action(
                    "Payment Created",
                    "Payment",
                    voucher_no
                )

                st.success(
                    f"✅ Payment {voucher_no} saved."
                )

            elif save_payment:

                st.error(
                    "Amount must be greater than zero."
                )


    # ========================================================
    # CONTRA
    # ========================================================

    with voucher_tab[4]:

        st.subheader("🔄 Contra Voucher")

        voucher_no = get_next_voucher_no("Contra")

        with st.form("contra_form"):

            contra_date = st.date_input(
                "Date",
                value=datetime.now().date(),
                key="contra_date"
            )

            from_account = st.selectbox(
                "From Account",
                [
                    "Cash",
                    "Bank"
                ],
                key="contra_from"
            )

            to_account = st.selectbox(
                "To Account",
                [
                    "Cash",
                    "Bank"
                ],
                key="contra_to"
            )

            amount = st.number_input(
                "Amount",
                min_value=0.0,
                key="contra_amount"
            )

            narration = st.text_area(
                "Narration",
                key="contra_narration"
            )

            save_contra = st.form_submit_button(
                "💾 SAVE CONTRA"
            )

            if save_contra:

                if from_account == to_account:

                    st.error(
                        "From and To accounts cannot be same."
                    )

                elif amount <= 0:

                    st.error(
                        "Amount must be greater than zero."
                    )

                else:

                    save_transaction(
                        "Contra",
                        voucher_no,
                        str(contra_date),
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
                        0,
                        amount,
                        "Internal Transfer",
                        to_account,
                        from_account,
                        narration
                    )

                    post_ledger(
                        to_account,
                        "Cash/Bank",
                        "Contra",
                        voucher_no,
                        narration or "Contra Transfer",
                        amount,
                        0
                    )

                    post_ledger(
                        from_account,
                        "Cash/Bank",
                        "Contra",
                        voucher_no,
                        narration or "Contra Transfer",
                        0,
                        amount
                    )

                    log_action(
                        "Contra Created",
                        "Contra",
                        voucher_no
                    )

                    st.success(
                        f"✅ Contra {voucher_no} saved."
                    )


    # ========================================================
    # JOURNAL
    # ========================================================

    with voucher_tab[5]:

        st.subheader("📘 Journal Voucher")

        voucher_no = get_next_voucher_no("Journal")

        with st.form("journal_form"):

            journal_date = st.date_input(
                "Date",
                value=datetime.now().date(),
                key="journal_date"
            )

            debit_account = st.text_input(
                "Debit Account",
                key="journal_debit"
            )

            credit_account = st.text_input(
                "Credit Account",
                key="journal_credit"
            )

            amount = st.number_input(
                "Amount",
                min_value=0.0,
                key="journal_amount"
            )

            narration = st.text_area(
                "Narration",
                key="journal_narration"
            )

            save_journal = st.form_submit_button(
                "💾 SAVE JOURNAL"
            )

            if save_journal:

                if not debit_account.strip():

                    st.error(
                        "Debit account required."
                    )

                elif not credit_account.strip():

                    st.error(
                        "Credit account required."
                    )

                elif amount <= 0:

                    st.error(
                        "Amount must be greater than zero."
                    )

                else:

                    save_transaction(
                        "Journal",
                        voucher_no,
                        str(journal_date),
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
                        0,
                        amount,
                        "Journal",
                        debit_account,
                        credit_account,
                        narration
                    )

                    post_ledger(
                        debit_account,
                        "Ledger",
                        "Journal",
                        voucher_no,
                        narration or "Journal Entry",
                        amount,
                        0
                    )

                    post_ledger(
                        credit_account,
                        "Ledger",
                        "Journal",
                        voucher_no,
                        narration or "Journal Entry",
                        0,
                        amount
                    )

                    log_action(
                        "Journal Created",
                        "Journal",
                        voucher_no
                    )

                    st.success(
                        f"✅ Journal {voucher_no} saved."
             # ============================================================
# SALES RETURN
# ============================================================

elif menu == "↩️ Sales Return":

    st.subheader("↩️ Sales Return")

    conn = get_db()

    items_df = pd.read_sql_query("""
        SELECT item_name, unit, hsn_sac, gst_rate, sale_price
        FROM items
        WHERE user_mobile=? AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=? AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if items_df.empty:
        st.warning("⚠️ प्रथम Item Master मध्ये Item तयार करा.")
        st.stop()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Customer तयार करा.")
        st.stop()

    with st.form("sales_return_form"):

        c1, c2, c3 = st.columns(3)

        return_date = c1.date_input(
            "Return Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Return Voucher No.",
            value="SR-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Customer",
            parties_df["party_name"].tolist()
        )

        c1, c2, c3, c4 = st.columns(4)

        item = c1.selectbox(
            "Item",
            items_df["item_name"].tolist()
        )

        selected_item = items_df[
            items_df["item_name"] == item
        ].iloc[0]

        unit = c2.text_input(
            "Unit",
            value=str(selected_item["unit"])
        )

        hsn = c3.text_input(
            "HSN / SAC",
            value=str(selected_item["hsn_sac"] or "")
        )

        gst_rate = c4.number_input(
            "GST %",
            min_value=0.0,
            max_value=28.0,
            value=float(selected_item["gst_rate"] or 0)
        )

        c1, c2, c3 = st.columns(3)

        qty = c1.number_input(
            "Return Quantity",
            min_value=0.0,
            step=1.0
        )

        rate = c2.number_input(
            "Sales Rate",
            min_value=0.0,
            value=float(selected_item["sale_price"] or 0)
        )

        discount = c3.number_input(
            "Discount",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save_return = st.form_submit_button(
            "💾 SAVE SALES RETURN"
        )

        if save_return:

            if qty <= 0:
                st.error("❌ Return quantity 0 पेक्षा जास्त असावी.")

            elif rate <= 0:
                st.error("❌ Sales rate enter करा.")

            else:

                taxable = (qty * rate) - discount

                gst_amount = taxable * gst_rate / 100

                cgst = gst_amount / 2
                sgst = gst_amount / 2

                total = taxable + gst_amount

                conn = get_db()

                # Transaction Entry
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
                    mob,
                    "Sales Return",
                    voucher_no,
                    str(return_date),
                    party,
                    item,
                    unit,
                    hsn,
                    qty,
                    rate,
                    discount,
                    taxable,
                    gst_rate,
                    cgst,
                    sgst,
                    0,
                    total,
                    "Debit",
                    narration,
                    now()
                ))

                # Stock वाढवणे
                conn.execute("""
                    UPDATE items
                    SET current_stock = current_stock + ?
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    qty,
                    mob,
                    item
                ))

                # Stock Movement
                current_stock_row = conn.execute("""
                    SELECT current_stock
                    FROM items
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    mob,
                    item
                )).fetchone()

                balance_qty = (
                    current_stock_row[0]
                    if current_stock_row
                    else 0
                )

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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(return_date),
                    item,
                    "Main Store",
                    "Sales Return",
                    voucher_no,
                    qty,
                    0,
                    balance_qty,
                    rate,
                    now()
                ))

                # Customer Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(return_date),
                    party,
                    "Customer",
                    "Sales Return",
                    voucher_no,
                    item,
                    0,
                    total,
                    total,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Sales Return Created",
                    "Sales Return",
                    voucher_no
                )

                st.success(
                    f"✅ Sales Return {voucher_no} saved successfully."
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Taxable Amount",
                    money(taxable)
                )

                c2.metric(
                    "GST",
                    money(gst_amount)
                )

                c3.metric(
                    "Return Total",
                    money(total)
                )


# ============================================================
# SALES RETURN HISTORY
# ============================================================

elif menu == "📋 Sales Return History":

    st.subheader("📋 Sales Return History")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("📭 Sales Return records नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Sales Return",
            money(df["Total"].sum())
        )


# ============================================================
# PURCHASE RETURN
# ============================================================

elif menu == "↩️ Purchase Return":

    st.subheader("↩️ Purchase Return")

    conn = get_db()

    items_df = pd.read_sql_query("""
        SELECT item_name, unit, hsn_sac, gst_rate, purchase_price
        FROM items
        WHERE user_mobile=? AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=? AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if items_df.empty:
        st.warning("⚠️ प्रथम Item Master मध्ये Item तयार करा.")
        st.stop()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Supplier तयार करा.")
        st.stop()

    with st.form("purchase_return_form"):

        c1, c2, c3 = st.columns(3)

        return_date = c1.date_input(
            "Return Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Return Voucher No.",
            value="PR-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Supplier",
            parties_df["party_name"].tolist()
        )

        c1, c2, c3, c4 = st.columns(4)

        item = c1.selectbox(
            "Item",
            items_df["item_name"].tolist()
        )

        selected_item = items_df[
            items_df["item_name"] == item
        ].iloc[0]

        unit = c2.text_input(
            "Unit",
            value=str(selected_item["unit"])
        )

        hsn = c3.text_input(
            "HSN / SAC",
            value=str(selected_item["hsn_sac"] or "")
        )

        gst_rate = c4.number_input(
            "GST %",
            min_value=0.0,
            max_value=28.0,
            value=float(selected_item["gst_rate"] or 0)
        )

        c1, c2, c3 = st.columns(3)

        qty = c1.number_input(
            "Return Quantity",
            min_value=0.0,
            step=1.0
        )

        rate = c2.number_input(
            "Purchase Rate",
            min_value=0.0,
            value=float(selected_item["purchase_price"] or 0)
        )

        discount = c3.number_input(
            "Discount",
            min_value=0.0
        )

        narration = st.text_area(
            "Narration"
        )

        save_return = st.form_submit_button(
            "💾 SAVE PURCHASE RETURN"
        )

        if save_return:

            if qty <= 0:
                st.error("❌ Return quantity 0 पेक्षा जास्त असावी.")

            elif rate <= 0:
                st.error("❌ Purchase rate enter करा.")

            else:

                taxable = (qty * rate) - discount

                gst_amount = taxable * gst_rate / 100

                cgst = gst_amount / 2
                sgst = gst_amount / 2

                total = taxable + gst_amount

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
                    mob,
                    "Purchase Return",
                    voucher_no,
                    str(return_date),
                    party,
                    item,
                    unit,
                    hsn,
                    qty,
                    rate,
                    discount,
                    taxable,
                    gst_rate,
                    cgst,
                    sgst,
                    0,
                    total,
                    "Credit",
                    narration,
                    now()
                ))

                # Stock कमी करणे
                conn.execute("""
                    UPDATE items
                    SET current_stock = current_stock - ?
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    qty,
                    mob,
                    item
                ))

                current_stock_row = conn.execute("""
                    SELECT current_stock
                    FROM items
                    WHERE user_mobile=?
                    AND item_name=?
                """, (
                    mob,
                    item
                )).fetchone()

                balance_qty = (
                    current_stock_row[0]
                    if current_stock_row
                    else 0
                )

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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(return_date),
                    item,
                    "Main Store",
                    "Purchase Return",
                    voucher_no,
                    0,
                    qty,
                    balance_qty,
                    rate,
                    now()
                ))

                # Supplier Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(return_date),
                    party,
                    "Supplier",
                    "Purchase Return",
                    voucher_no,
                    item,
                    total,
                    0,
                    total,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Purchase Return Created",
                    "Purchase Return",
                    voucher_no
                )

                st.success(
                    f"✅ Purchase Return {voucher_no} saved successfully."
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Taxable Amount",
                    money(taxable)
                )

                c2.metric(
                    "GST",
                    money(gst_amount)
                )

                c3.metric(
                    "Return Total",
                    money(total)
                )


# ============================================================
# PURCHASE RETURN HISTORY
# ============================================================

elif menu == "📋 Purchase Return History":

    st.subheader("📋 Purchase Return History")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("📭 Purchase Return records नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Purchase Return",
            money(df["Total"].sum())
                    )
    # ============================================================
# RECEIPT
# ============================================================

elif menu == "💰 Receipt":

    st.subheader("💰 Receipt")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Customer तयार करा.")
        st.stop()

    with st.form("receipt_form"):

        c1, c2, c3 = st.columns(3)

        receipt_date = c1.date_input(
            "Receipt Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Receipt Voucher No.",
            value="REC-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Received From",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_receipt = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save_receipt:

            if amount <= 0:
                st.error("❌ Amount 0 पेक्षा जास्त असावी.")

            else:

                conn = get_db()

                # Transaction Entry
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
                    mob,
                    "Receipt",
                    voucher_no,
                    str(receipt_date),
                    party,
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
                    narration,
                    now()
                ))

                # Customer Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(receipt_date),
                    party,
                    "Customer",
                    "Receipt",
                    voucher_no,
                    narration or "Receipt",
                    0,
                    amount,
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
                    f"✅ Receipt {voucher_no} saved successfully."
                )

                c1, c2 = st.columns(2)

                c1.metric(
                    "Received Amount",
                    money(amount)
                )

                c2.metric(
                    "Payment Mode",
                    payment_mode
                )


# ============================================================
# RECEIPT HISTORY
# ============================================================

elif menu == "📋 Receipt History":

    st.subheader("📋 Receipt History")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Receipt'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("📭 Receipt records नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Receipt",
            money(df["Amount"].sum())
        )


# ============================================================
# PAYMENT
# ============================================================

elif menu == "💸 Payment":

    st.subheader("💸 Payment")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Supplier तयार करा.")
        st.stop()

    with st.form("payment_form"):

        c1, c2, c3 = st.columns(3)

        payment_date = c1.date_input(
            "Payment Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Payment Voucher No.",
            value="PAY-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Paid To",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_payment = st.form_submit_button(
            "💾 SAVE PAYMENT"
        )

        if save_payment:

            if amount <= 0:
                st.error("❌ Amount 0 पेक्षा जास्त असावी.")

            else:

                conn = get_db()

                # Transaction Entry
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
                    mob,
                    "Payment",
                    voucher_no,
                    str(payment_date),
                    party,
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
                    narration,
                    now()
                ))

                # Supplier Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(payment_date),
                    party,
                    "Supplier",
                    "Payment",
                    voucher_no,
                    narration or "Payment",
                    amount,
                    0,
                    amount,
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
                    f"✅ Payment {voucher_no} saved successfully."
                )

                c1, c2 = st.columns(2)

                c1.metric(
                    "Paid Amount",
                    money(amount)
                )

                c2.metric(
                    "Payment Mode",
                    payment_mode
                )


# ============================================================
# PAYMENT HISTORY
# ============================================================

elif menu == "📋 Payment History":

    st.subheader("📋 Payment History")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Payment'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("📭 Payment records नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Payment",
            money(df["Amount"].sum())
                    )                # ============================================================
# RECEIPT
# ============================================================

elif menu == "💰 Receipt":

    st.subheader("💰 Receipt")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Customer तयार करा.")
        st.stop()

    with st.form("receipt_form"):

        c1, c2, c3 = st.columns(3)

        receipt_date = c1.date_input(
            "Receipt Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Receipt Voucher No.",
            value="REC-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Received From",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_receipt = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save_receipt:

            if amount <= 0:
                st.error("❌ Amount 0 पेक्षा जास्त असावी.")

            else:

                conn = get_db()

                # Transaction Entry
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
                    mob,
                    "Receipt",
                    voucher_no,
                    str(receipt_date),
                    party,
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
                    narration,
                    now()
                ))

                # Customer Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(receipt_date),
                    party,
                    "Customer",
                    "Receipt",
                    voucher_no,
                    narration or "Receipt",
                    0,
                    amount,
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
                    f"✅ Receipt {voucher_no} saved successfully."
                )

                c1, c2 = st.columns(2)

                c1.metric(
                    "Received Amount",
                    money(amount)
                )

                c2.metric(
                    "Payment Mode",
                    payment_mode
                )


# ============================================================
# RECEIPT HISTORY
# ============================================================

elif menu == "📋 Receipt History":

    st.subheader("📋 Receipt History")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Receipt'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("📭 Receipt records नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Receipt",
            money(df["Amount"].sum())
        )


# ============================================================
# PAYMENT
# ============================================================

elif menu == "💸 Payment":

    st.subheader("💸 Payment")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Supplier तयार करा.")
        st.stop()

    with st.form("payment_form"):

        c1, c2, c3 = st.columns(3)

        payment_date = c1.date_input(
            "Payment Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Payment Voucher No.",
            value="PAY-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Paid To",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_payment = st.form_submit_button(
            "💾 SAVE PAYMENT"
        )

        if save_payment:

            if amount <= 0:
                st.error("❌ Amount 0 पेक्षा जास्त असावी.")

            else:

                conn = get_db()

                # Transaction Entry
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
                    mob,
                    "Payment",
                    voucher_no,
                    str(payment_date),
                    party,
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
                    narration,
                    now()
                ))

                # Supplier Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(payment_date),
                    party,
                    "Supplier",
                    "Payment",
                    voucher_no,
                    narration or "Payment",
                    amount,
                    0,
                    amount,
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
                    f"✅ Payment {voucher_no} saved successfully."
                )

                c1, c2 = st.columns(2)

                c1.metric(
                    "Paid Amount",
                    money(amount)
                )

                c2.metric(
                    "Payment Mode",
                    payment_mode
                )


# ============================================================
# PAYMENT HISTORY
# ============================================================

elif menu == "📋 Payment History":

    st.subheader("📋 Payment History")

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Payment'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if df.empty:

        st.info("📭 Payment records नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Payment",
            money(df["Amount"].sum())
        )
# ============================================================
# LEDGER
# ============================================================

elif menu == "📒 Ledger":

    st.subheader("📒 Party Ledger")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:
        st.warning("⚠️ प्रथम Party Master मध्ये Party तयार करा.")
        st.stop()

    selected_party = st.selectbox(
        "Select Party",
        parties_df["party_name"].tolist()
    )

    conn = get_db()

    ledger_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher,
            voucher_no AS Voucher_No,
            particulars AS Particulars,
            debit AS Debit,
            credit AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_name=?
        ORDER BY id ASC
    """, conn, params=(mob, selected_party))

    conn.close()

    if ledger_df.empty:

        st.info("📭 या Party चे Ledger records उपलब्ध नाहीत.")

    else:

        ledger_df["Debit"] = ledger_df["Debit"].fillna(0)
        ledger_df["Credit"] = ledger_df["Credit"].fillna(0)

        ledger_df["Balance"] = (
            ledger_df["Debit"].cumsum()
            - ledger_df["Credit"].cumsum()
        )

        st.dataframe(
            ledger_df,
            use_container_width=True,
            hide_index=True
        )

        total_debit = ledger_df["Debit"].sum()
        total_credit = ledger_df["Credit"].sum()
        balance = total_debit - total_credit

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Debit",
            money(total_debit)
        )

        c2.metric(
            "Total Credit",
            money(total_credit)
        )

        c3.metric(
            "Balance",
            money(abs(balance))
        )


# ============================================================
# DAY BOOK
# ============================================================

elif menu == "📖 Day Book":

    st.subheader("📖 Day Book")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if df.empty:

        st.info("📭 या Date Range मध्ये कोणतेही transaction नाहीत.")

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        total_amount = df["Amount"].fillna(0).sum()

        st.metric(
            "Total Transactions",
            money(total_amount)
        )


# ============================================================
# OUTSTANDING
# ============================================================

elif menu == "📊 Outstanding":

    st.subheader("📊 Outstanding")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:
        st.warning("⚠️ Party Master मध्ये Party उपलब्ध नाही.")
        st.stop()

    rows = []

    conn = get_db()

    for party in parties_df["party_name"].tolist():

        ledger_data = pd.read_sql_query("""
            SELECT
                COALESCE(SUM(debit), 0) AS debit,
                COALESCE(SUM(credit), 0) AS credit
            FROM ledger
            WHERE user_mobile=?
            AND account_name=?
        """, conn, params=(mob, party))

        debit = float(ledger_data.iloc[0]["debit"])
        credit = float(ledger_data.iloc[0]["credit"])

        balance = debit - credit

        if balance != 0:

            rows.append({
                "Party": party,
                "Debit": debit,
                "Credit": credit,
                "Balance": abs(balance),
                "Status": (
                    "Receivable"
                    if balance > 0
                    else "Payable"
                )
            })

    conn.close()

    if not rows:

        st.success("✅ कोणतेही Outstanding Balance नाही.")

    else:

        outstanding_df = pd.DataFrame(rows)

        st.dataframe(
            outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        receivable = outstanding_df.loc[
            outstanding_df["Status"] == "Receivable",
            "Balance"
        ].sum()

        payable = outstanding_df.loc[
            outstanding_df["Status"] == "Payable",
            "Balance"
        ].sum()

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Receivable",
            money(receivable)
        )

        c2.metric(
            "Total Payable",
            money(payable)
        )


# ============================================================
# STOCK SUMMARY
# ============================================================

elif menu == "📦 Stock Summary":

    st.subheader("📦 Stock Summary")

    conn = get_db()

    stock_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            hsn_sac AS HSN_SAC,
            current_stock AS Current_Stock,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if stock_df.empty:

        st.info("📭 Stock records उपलब्ध नाहीत.")

    else:

        stock_df["Current_Stock"] = (
            stock_df["Current_Stock"].fillna(0)
        )

        stock_df["Stock Value"] = (
            stock_df["Current_Stock"]
            * stock_df["Purchase_Rate"].fillna(0)
        )

        st.dataframe(
            stock_df,
            use_container_width=True,
            hide_index=True
        )

        total_stock_value = stock_df["Stock Value"].sum()

        st.metric(
            "Total Stock Value",
            money(total_stock_value)
        )


# ============================================================
# STOCK MOVEMENT
# ============================================================

elif menu == "📋 Stock Movement":

    st.subheader("📋 Stock Movement")

    conn = get_db()

    items_df = pd.read_sql_query("""
        SELECT item_name
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if items_df.empty:
        st.warning("⚠️ Item Master मध्ये Item उपलब्ध नाही.")
        st.stop()

    item_filter = st.selectbox(
        "Select Item",
        ["All Items"] + items_df["item_name"].tolist()
    )

    conn = get_db()

    if item_filter == "All Items":

        movement_df = pd.read_sql_query("""
            SELECT
                date AS Date,
                item_name AS Item,
                movement_type AS Movement,
                reference_no AS Reference_No,
                qty_in AS Qty_In,
                qty_out AS Qty_Out,
                balance_qty AS Balance,
                rate AS Rate
            FROM stock_movements
            WHERE user_mobile=?
            ORDER BY id DESC
        """, conn, params=(mob,))

    else:

        movement_df = pd.read_sql_query("""
            SELECT
                date AS Date,
                item_name AS Item,
                movement_type AS Movement,
                reference_no AS Reference_No,
                qty_in AS Qty_In,
                qty_out AS Qty_Out,
                balance_qty AS Balance,
                rate AS Rate
            FROM stock_movements
            WHERE user_mobile=?
            AND item_name=?
            ORDER BY id DESC
        """, conn, params=(mob, item_filter))

    conn.close()

    if movement_df.empty:

        st.info("📭 Stock Movement records नाहीत.")

    else:

        st.dataframe(
            movement_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# GST REPORT
# ============================================================

elif menu == "📊 GST Report":

    st.subheader("📊 GST Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    gst_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            party_name AS Party,
            taxable_amount AS Taxable,
            gst_rate AS GST_Rate,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND gst_rate > 0
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if gst_df.empty:

        st.info("📭 GST records नाहीत.")

    else:

        st.dataframe(
            gst_df,
            use_container_width=True,
            hide_index=True
        )

        taxable_total = gst_df["Taxable"].fillna(0).sum()
        cgst_total = gst_df["CGST"].fillna(0).sum()
        sgst_total = gst_df["SGST"].fillna(0).sum()
        igst_total = gst_df["IGST"].fillna(0).sum()
        total_gst = (
            cgst_total
            + sgst_total
            + igst_total
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Taxable",
            money(taxable_total)
        )

        c2.metric(
            "CGST",
            money(cgst_total)
        )

        c3.metric(
            "SGST",
            money(sgst_total)
        )

        c4.metric(
            "Total GST",
            money(total_gst)
        )


# ============================================================
# SALES REPORT
# ============================================================

elif menu == "📈 Sales Report":

    st.subheader("📈 Sales Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Invoice_No,
            party_name AS Customer,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_df.empty:

        st.info("📭 Sales records नाहीत.")

    else:

        st.dataframe(
            sales_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable Sales",
            money(sales_df["Taxable"].fillna(0).sum())
        )

        c2.metric(
            "Total GST",
            money(
                sales_df["CGST"].fillna(0).sum()
                + sales_df["SGST"].fillna(0).sum()
                + sales_df["IGST"].fillna(0).sum()
            )
        )

        c3.metric(
            "Total Sales",
            money(sales_df["Total"].fillna(0).sum())
        )


# ============================================================
# PURCHASE REPORT
# ============================================================

elif menu == "📉 Purchase Report":

    st.subheader("📉 Purchase Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Invoice_No,
            party_name AS Supplier,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_df.empty:

        st.info("📭 Purchase records नाहीत.")

    else:

        st.dataframe(
            purchase_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable Purchase",
            money(purchase_df["Taxable"].fillna(0).sum())
        )

        c2.metric(
            "Total GST",
            money(
                purchase_df["CGST"].fillna(0).sum()
                + purchase_df["SGST"].fillna(0).sum()
                + purchase_df["IGST"].fillna(0).sum()
            )
        )

        c3.metric(
            "Total Purchase",
            money(purchase_df["Total"].fillna(0).sum())
        )
  # ============================================================
# PROFIT & LOSS
# ============================================================

elif menu == "📊 Profit & Loss":

    st.subheader("📊 Profit & Loss")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_data = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(taxable_amount), 0) AS amount
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    purchase_data = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(taxable_amount), 0) AS amount
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    sales_return_data = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(taxable_amount), 0) AS amount
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    purchase_return_data = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(taxable_amount), 0) AS amount
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    sales = float(sales_data.iloc[0]["amount"])
    purchase = float(purchase_data.iloc[0]["amount"])
    sales_return = float(sales_return_data.iloc[0]["amount"])
    purchase_return = float(purchase_return_data.iloc[0]["amount"])

    net_sales = sales - sales_return
    net_purchase = purchase - purchase_return

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
        "Gross Profit / Loss",
        money(abs(gross_profit))
    )

    st.divider()

    profit_loss_df = pd.DataFrame([
        {
            "Particulars": "Sales",
            "Amount": sales
        },
        {
            "Particulars": "Less: Sales Return",
            "Amount": sales_return
        },
        {
            "Particulars": "Net Sales",
            "Amount": net_sales
        },
        {
            "Particulars": "Purchase",
            "Amount": purchase
        },
        {
            "Particulars": "Less: Purchase Return",
            "Amount": purchase_return
        },
        {
            "Particulars": "Net Purchase",
            "Amount": net_purchase
        },
        {
            "Particulars": (
                "Gross Profit"
                if gross_profit >= 0
                else "Gross Loss"
            ),
            "Amount": abs(gross_profit)
        }
    ])

    st.dataframe(
        profit_loss_df,
        use_container_width=True,
        hide_index=True
    )

    if gross_profit >= 0:
        st.success(
            f"✅ Gross Profit: {money(gross_profit)}"
        )
    else:
        st.error(
            f"❌ Gross Loss: {money(abs(gross_profit))}"
        )


# ============================================================
# TRIAL BALANCE
# ============================================================

elif menu == "⚖️ Trial Balance":

    st.subheader("⚖️ Trial Balance")

    conn = get_db()

    trial_df = pd.read_sql_query("""
        SELECT
            account_name AS Account,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        GROUP BY account_name
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if trial_df.empty:

        st.info(
            "📭 Trial Balance साठी records उपलब्ध नाहीत."
        )

    else:

        trial_df["Debit"] = (
            trial_df["Debit"].fillna(0)
        )

        trial_df["Credit"] = (
            trial_df["Credit"].fillna(0)
        )

        total_debit = trial_df["Debit"].sum()
        total_credit = trial_df["Credit"].sum()

        trial_df["Debit"] = trial_df["Debit"].round(2)
        trial_df["Credit"] = trial_df["Credit"].round(2)

        st.dataframe(
            trial_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Debit",
            money(total_debit)
        )

        c2.metric(
            "Total Credit",
            money(total_credit)
        )

        if round(total_debit, 2) == round(total_credit, 2):

            st.success(
                "✅ Trial Balance is Balanced."
            )

        else:

            difference = abs(
                total_debit - total_credit
            )

            st.warning(
                f"⚠️ Trial Balance Difference: "
                f"{money(difference)}"
            )


# ============================================================
# BALANCE SHEET
# ============================================================

elif menu == "⚖️ Balance Sheet":

    st.subheader("⚖️ Balance Sheet")

    conn = get_db()

    ledger_df = pd.read_sql_query("""
        SELECT
            account_name AS Account,
            account_type AS Account_Type,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        GROUP BY account_name, account_type
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if ledger_df.empty:

        st.info(
            "📭 Balance Sheet साठी records उपलब्ध नाहीत."
        )

    else:

        ledger_df["Debit"] = (
            ledger_df["Debit"].fillna(0)
        )

        ledger_df["Credit"] = (
            ledger_df["Credit"].fillna(0)
        )

        assets = []
        liabilities = []

        for _, row in ledger_df.iterrows():

            balance = (
                float(row["Debit"])
                - float(row["Credit"])
            )

            if balance == 0:
                continue

            account_type = str(
                row["Account_Type"]
            ).lower()

            if (
                "supplier" in account_type
                or "liability" in account_type
            ):

                liabilities.append({
                    "Account": row["Account"],
                    "Amount": abs(balance)
                })

            else:

                assets.append({
                    "Account": row["Account"],
                    "Amount": abs(balance)
                })

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### 🏦 Assets")

            if assets:

                assets_df = pd.DataFrame(assets)

                st.dataframe(
                    assets_df,
                    use_container_width=True,
                    hide_index=True
                )

                total_assets = (
                    assets_df["Amount"].sum()
                )

            else:

                st.info("No Assets")

                total_assets = 0

            st.metric(
                "Total Assets",
                money(total_assets)
            )

        with col2:

            st.markdown("### 📋 Liabilities")

            if liabilities:

                liabilities_df = pd.DataFrame(
                    liabilities
                )

                st.dataframe(
                    liabilities_df,
                    use_container_width=True,
                    hide_index=True
                )

                total_liabilities = (
                    liabilities_df["Amount"].sum()
                )

            else:

                st.info("No Liabilities")

                total_liabilities = 0

            st.metric(
                "Total Liabilities",
                money(total_liabilities)
            )


# ============================================================
# GST SUMMARY
# ============================================================

elif menu == "🧾 GST Summary":

    st.subheader("🧾 GST Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    gst_summary = pd.read_sql_query("""
        SELECT
            gst_rate AS GST_Rate,
            COALESCE(SUM(taxable_amount), 0)
                AS Taxable,
            COALESCE(SUM(cgst), 0)
                AS CGST,
            COALESCE(SUM(sgst), 0)
                AS SGST,
            COALESCE(SUM(igst), 0)
                AS IGST,
            COALESCE(SUM(total_amount), 0)
                AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND gst_rate > 0
        GROUP BY gst_rate
        ORDER BY gst_rate
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if gst_summary.empty:

        st.info(
            "📭 GST Summary records नाहीत."
        )

    else:

        st.dataframe(
            gst_summary,
            use_container_width=True,
            hide_index=True
        )

        total_taxable = (
            gst_summary["Taxable"].sum()
        )

        total_cgst = (
            gst_summary["CGST"].sum()
        )

        total_sgst = (
            gst_summary["SGST"].sum()
        )

        total_igst = (
            gst_summary["IGST"].sum()
        )

        total_gst = (
            total_cgst
            + total_sgst
            + total_igst
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Taxable",
            money(total_taxable)
        )

        c2.metric(
            "CGST",
            money(total_cgst)
        )

        c3.metric(
            "SGST",
            money(total_sgst)
        )

        c4.metric(
            "Total GST",
            money(total_gst)
        )


# ============================================================
# GST RETURN SUMMARY
# ============================================================

elif menu == "🧾 GST Return Summary":

    st.subheader("🧾 GST Return Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    gst_return_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            COUNT(*) AS Transactions,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND voucher_type IN
        (
            'Sales',
            'Sales Return',
            'Purchase',
            'Purchase Return'
        )
        GROUP BY voucher_type
        ORDER BY voucher_type
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if gst_return_df.empty:

        st.info(
            "📭 GST Return साठी records नाहीत."
        )

    else:

        st.dataframe(
            gst_return_df,
            use_container_width=True,
            hide_index=True
        )

        total_taxable = (
            gst_return_df["Taxable"].sum()
        )

        total_cgst = (
            gst_return_df["CGST"].sum()
        )

        total_sgst = (
            gst_return_df["SGST"].sum()
        )

        total_igst = (
            gst_return_df["IGST"].sum()
        )

        total_amount = (
            gst_return_df["Total"].sum()
        )

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(total_taxable)
        )

        c2.metric(
            "Total GST",
            money(
                total_cgst
                + total_sgst
                + total_igst
            )
        )

        c3.metric(
            "Total Amount",
            money(total_amount)
        )


# ============================================================
# EXPENSE
# ============================================================

elif menu == "💳 Expense":

    st.subheader("💳 Expense")

    with st.form("expense_form"):

        c1, c2, c3 = st.columns(3)

        expense_date = c1.date_input(
            "Expense Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Expense Voucher No.",
            value="EXP-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        payment_mode = c3.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        c1, c2 = st.columns(2)

        expense_head = c1.text_input(
            "Expense Head",
            placeholder="Rent / Electricity / Travel / Salary"
        )

        amount = c2.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        narration = st.text_area(
            "Narration"
        )

        save_expense = st.form_submit_button(
            "💾 SAVE EXPENSE"
        )

        if save_expense:

            if not expense_head.strip():
                st.error(
                    "❌ Expense Head enter करा."
                )

            elif amount <= 0:
                st.error(
                    "❌ Amount 0 पेक्षा जास्त असावी."
                )

            else:

                conn = get_db()

                # Transaction Entry
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
                    mob,
                    "Expense",
                    voucher_no,
                    str(expense_date),
                    expense_head,
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
                    narration,
                    now()
                ))

                # Expense Ledger
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
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(expense_date),
                    expense_head,
                    "Expense",
                    "Expense",
                    voucher_no,
                    narration or expense_head,
                    amount,
                    0,
                    amount,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Expense Created",
                    "Expense",
                    voucher_no
                )

                st.success(
                    f"✅ Expense {voucher_no} saved successfully."
                )

                st.metric(
                    "Expense Amount",
                    money(amount)
                )


# ============================================================
# EXPENSE HISTORY
# ============================================================

elif menu == "📋 Expense History":

    st.subheader("📋 Expense History")

    conn = get_db()

    expense_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Expense_Head,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Expense'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if expense_df.empty:

        st.info(
            "📭 Expense records नाहीत."
        )

    else:

        st.dataframe(
            expense_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Expense",
            money(
                expense_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# CASH BOOK
# ============================================================

elif menu == "📒 Cash Book":

    st.subheader("📒 Cash Book")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    cash_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher,
            voucher_no AS Voucher_No,
            party_name AS Party,
            debit AS Debit,
            credit AS Credit,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM ledger
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND (
            voucher_type IN
            (
                'Receipt',
                'Payment',
                'Expense'
            )
            OR payment_mode='Cash'
        )
        ORDER BY date ASC, id ASC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if cash_df.empty:

        st.info("📭 Cash Book मध्ये records नाहीत.")

    else:

        cash_df["Debit"] = (
            cash_df["Debit"].fillna(0)
        )

        cash_df["Credit"] = (
            cash_df["Credit"].fillna(0)
        )

        cash_df["Balance"] = (
            cash_df["Debit"].cumsum()
            - cash_df["Credit"].cumsum()
        )

        st.dataframe(
            cash_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Debit",
            money(cash_df["Debit"].sum())
        )

        c2.metric(
            "Total Credit",
            money(cash_df["Credit"].sum())
        )

        c3.metric(
            "Closing Balance",
            money(abs(cash_df["Balance"].iloc[-1]))
        )


# ============================================================
# BANK BOOK
# ============================================================

elif menu == "🏦 Bank Book":

    st.subheader("🏦 Bank Book")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    bank_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher,
            voucher_no AS Voucher_No,
            party_name AS Party,
            debit AS Debit,
            credit AS Credit,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM ledger
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND payment_mode IN
        (
            'Bank',
            'UPI',
            'Cheque',
            'NEFT',
            'RTGS'
        )
        ORDER BY date ASC, id ASC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if bank_df.empty:

        st.info("📭 Bank Book मध्ये records नाहीत.")

    else:

        bank_df["Debit"] = (
            bank_df["Debit"].fillna(0)
        )

        bank_df["Credit"] = (
            bank_df["Credit"].fillna(0)
        )

        bank_df["Balance"] = (
            bank_df["Debit"].cumsum()
            - bank_df["Credit"].cumsum()
        )

        st.dataframe(
            bank_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Debit",
            money(bank_df["Debit"].sum())
        )

        c2.metric(
            "Total Credit",
            money(bank_df["Credit"].sum())
        )

        c3.metric(
            "Closing Balance",
            money(
                abs(
                    bank_df["Balance"].iloc[-1]
                )
            )
        )


# ============================================================
# DAILY SUMMARY
# ============================================================

elif menu == "📅 Daily Summary":

    st.subheader("📅 Daily Summary")

    selected_date = st.date_input(
        "Select Date",
        value=datetime.now().date()
    )

    conn = get_db()

    daily_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            COUNT(*) AS Transactions,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date=?
        GROUP BY voucher_type
        ORDER BY voucher_type
    """, conn, params=(
        mob,
        str(selected_date)
    ))

    conn.close()

    if daily_df.empty:

        st.info(
            "📭 या तारखेला कोणतेही transactions नाहीत."
        )

    else:

        st.dataframe(
            daily_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Daily Transaction Total",
            money(
                daily_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# MONTHLY SUMMARY
# ============================================================

elif menu == "📆 Monthly Summary":

    st.subheader("📆 Monthly Summary")

    selected_month = st.date_input(
        "Select Month",
        value=datetime.now().date()
    )

    month_value = selected_month.strftime("%Y-%m")

    conn = get_db()

    monthly_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            COUNT(*) AS Transactions,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND substr(date, 1, 7)=?
        GROUP BY voucher_type
        ORDER BY voucher_type
    """, conn, params=(
        mob,
        month_value
    ))

    conn.close()

    if monthly_df.empty:

        st.info(
            "📭 या महिन्यात कोणतेही transactions नाहीत."
        )

    else:

        st.dataframe(
            monthly_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Monthly Transaction Total",
            money(
                monthly_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# TRANSACTION REPORT
# ============================================================

elif menu == "📑 Transaction Report":

    st.subheader("📑 Transaction Report")

    c1, c2, c3 = st.columns(3)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    voucher_filter = c3.selectbox(
        "Voucher Type",
        [
            "All",
            "Sales",
            "Purchase",
            "Sales Return",
            "Purchase Return",
            "Receipt",
            "Payment",
            "Expense"
        ]
    )

    conn = get_db()

    if voucher_filter == "All":

        report_df = pd.read_sql_query("""
            SELECT
                date AS Date,
                voucher_type AS Voucher_Type,
                voucher_no AS Voucher_No,
                party_name AS Party,
                item_name AS Item,
                qty AS Quantity,
                rate AS Rate,
                discount AS Discount,
                taxable_amount AS Taxable,
                gst_rate AS GST_Rate,
                cgst AS CGST,
                sgst AS SGST,
                igst AS IGST,
                total_amount AS Total,
                payment_mode AS Payment_Mode,
                narration AS Narration
            FROM transactions
            WHERE user_mobile=?
            AND date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
        """, conn, params=(
            mob,
            str(from_date),
            str(to_date)
        ))

    else:

        report_df = pd.read_sql_query("""
            SELECT
                date AS Date,
                voucher_type AS Voucher_Type,
                voucher_no AS Voucher_No,
                party_name AS Party,
                item_name AS Item,
                qty AS Quantity,
                rate AS Rate,
                discount AS Discount,
                taxable_amount AS Taxable,
                gst_rate AS GST_Rate,
                cgst AS CGST,
                sgst AS SGST,
                igst AS IGST,
                total_amount AS Total,
                payment_mode AS Payment_Mode,
                narration AS Narration
            FROM transactions
            WHERE user_mobile=?
            AND date BETWEEN ? AND ?
            AND voucher_type=?
            ORDER BY date DESC, id DESC
        """, conn, params=(
            mob,
            str(from_date),
            str(to_date),
            voucher_filter
        ))

    conn.close()

    if report_df.empty:

        st.info(
            "📭 Records उपलब्ध नाहीत."
        )

    else:

        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True
        )

        total_taxable = (
            report_df["Taxable"]
            .fillna(0)
            .sum()
        )

        total_gst = (
            report_df["CGST"].fillna(0).sum()
            + report_df["SGST"].fillna(0).sum()
            + report_df["IGST"].fillna(0).sum()
        )

        total_amount = (
            report_df["Total"]
            .fillna(0)
            .sum()
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(total_taxable)
        )

        c2.metric(
            "Total GST",
            money(total_gst)
        )

        c3.metric(
            "Total Amount",
            money(total_amount)
        )


# ============================================================
# VOUCHER SUMMARY
# ============================================================

elif menu == "📊 Voucher Summary":

    st.subheader("📊 Voucher Summary")

    conn = get_db()

    voucher_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            COUNT(*) AS Total_Vouchers,
            COALESCE(SUM(total_amount), 0) AS Total_Amount
        FROM transactions
        WHERE user_mobile=?
        GROUP BY voucher_type
        ORDER BY voucher_type
    """, conn, params=(mob,))

    conn.close()

    if voucher_df.empty:

        st.info(
            "📭 Voucher records उपलब्ध नाहीत."
        )

    else:

        st.dataframe(
            voucher_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Voucher Amount",
            money(
                voucher_df["Total_Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# ITEM WISE SALES
# ============================================================

elif menu == "📦 Item Wise Sales":

    st.subheader("📦 Item Wise Sales Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    item_sales_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY item_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if item_sales_df.empty:

        st.info(
            "📭 Item Wise Sales records नाहीत."
        )

    else:

        st.dataframe(
            item_sales_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Quantity",
            f"{item_sales_df['Quantity'].sum():,.2f}"
        )

        c2.metric(
            "Total Sales",
            money(
                item_sales_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PARTY WISE SALES
# ============================================================

elif menu == "👥 Party Wise Sales":

    st.subheader("👥 Party Wise Sales Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    party_sales_df = pd.read_sql_query("""
        SELECT
            party_name AS Customer,
            COUNT(*) AS Invoices,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if party_sales_df.empty:

        st.info(
            "📭 Party Wise Sales records नाहीत."
        )

    else:

        st.dataframe(
            party_sales_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Sales",
            money(
                party_sales_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# ITEM WISE PURCHASE
# ============================================================

elif menu == "📦 Item Wise Purchase":

    st.subheader("📦 Item Wise Purchase Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    item_purchase_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        GROUP BY item_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if item_purchase_df.empty:

        st.info(
            "📭 Item Wise Purchase records नाहीत."
        )

    else:

        st.dataframe(
            item_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Quantity",
            f"{item_purchase_df['Quantity'].sum():,.2f}"
        )

        c2.metric(
            "Total Purchase",
            money(
                item_purchase_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PARTY WISE PURCHASE
# ============================================================

elif menu == "👥 Party Wise Purchase":

    st.subheader("👥 Party Wise Purchase Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    party_purchase_df = pd.read_sql_query("""
        SELECT
            party_name AS Supplier,
            COUNT(*) AS Invoices,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if party_purchase_df.empty:

        st.info(
            "📭 Party Wise Purchase records नाहीत."
        )

    else:

        st.dataframe(
            party_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Purchase",
            money(
                party_purchase_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# SALES RETURN REPORT
# ============================================================

elif menu == "📊 Sales Return Report":

    st.subheader("📊 Sales Return Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_return_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_return_df.empty:

        st.info(
            "📭 Sales Return records नाहीत."
        )

    else:

        st.dataframe(
            sales_return_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Sales Return",
            money(
                sales_return_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PURCHASE RETURN REPORT
# ============================================================

elif menu == "📊 Purchase Return Report":

    st.subheader("📊 Purchase Return Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_return_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_return_df.empty:

        st.info(
            "📭 Purchase Return records नाहीत."
        )

    else:

        st.dataframe(
            purchase_return_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Purchase Return",
            money(
                purchase_return_df["Total"]
                .fillna(0)
                .sum()
            )
                    )
    # ============================================================
# STOCK SUMMARY
# ============================================================

elif menu == "📦 Stock Summary":

    st.subheader("📦 Stock Summary")

    conn = get_db()

    stock_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            hsn_sac AS HSN_SAC,
            gst_rate AS GST_Rate,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate,
            current_stock AS Current_Stock
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if stock_df.empty:

        st.info("📭 Stock records उपलब्ध नाहीत.")

    else:

        stock_df["Current_Stock"] = (
            stock_df["Current_Stock"]
            .fillna(0)
        )

        st.dataframe(
            stock_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Items",
            len(stock_df)
        )

        c2.metric(
            "Total Stock Quantity",
            f"{stock_df['Current_Stock'].sum():,.2f}"
        )


# ============================================================
# STOCK MOVEMENT
# ============================================================

elif menu == "📊 Stock Movement":

    st.subheader("📊 Stock Movement")

    conn = get_db()

    movement_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            item_name AS Item,
            godown AS Godown,
            movement_type AS Movement,
            reference_no AS Reference_No,
            qty_in AS Qty_In,
            qty_out AS Qty_Out,
            balance_qty AS Balance,
            rate AS Rate
        FROM stock_movements
        WHERE user_mobile=?
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if movement_df.empty:

        st.info(
            "📭 Stock Movement records उपलब्ध नाहीत."
        )

    else:

        st.dataframe(
            movement_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# LOW STOCK REPORT
# ============================================================

elif menu == "⚠️ Low Stock Report":

    st.subheader("⚠️ Low Stock Report")

    minimum_stock = st.number_input(
        "Minimum Stock Level",
        min_value=0.0,
        value=5.0,
        step=1.0
    )

    conn = get_db()

    low_stock_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            current_stock AS Current_Stock,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        AND COALESCE(current_stock, 0) <= ?
        ORDER BY current_stock ASC, item_name
    """, conn, params=(
        mob,
        minimum_stock
    ))

    conn.close()

    if low_stock_df.empty:

        st.success(
            "✅ कोणतेही Low Stock Item नाही."
        )

    else:

        st.warning(
            f"⚠️ {len(low_stock_df)} items "
            "minimum stock level खाली आहेत."
        )

        st.dataframe(
            low_stock_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# OUT OF STOCK
# ============================================================

elif menu == "🚫 Out of Stock":

    st.subheader("🚫 Out of Stock")

    conn = get_db()

    out_stock_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            hsn_sac AS HSN_SAC,
            gst_rate AS GST_Rate,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate,
            current_stock AS Current_Stock
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        AND COALESCE(current_stock, 0) <= 0
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if out_stock_df.empty:

        st.success(
            "✅ कोणतेही Out of Stock Item नाही."
        )

    else:

        st.error(
            f"🚫 {len(out_stock_df)} items Out of Stock आहेत."
        )

        st.dataframe(
            out_stock_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# LEDGER REPORT
# ============================================================

elif menu == "📒 Ledger Report":

    st.subheader("📒 Ledger Report")

    conn = get_db()

    accounts_df = pd.read_sql_query("""
        SELECT DISTINCT account_name
        FROM ledger
        WHERE user_mobile=?
        AND account_name IS NOT NULL
        AND account_name != ''
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if accounts_df.empty:

        st.info("📭 Ledger accounts उपलब्ध नाहीत.")

    else:

        account = st.selectbox(
            "Select Account",
            accounts_df["account_name"].tolist()
        )

        c1, c2 = st.columns(2)

        from_date = c1.date_input(
            "From Date",
            value=datetime.now().date()
        )

        to_date = c2.date_input(
            "To Date",
            value=datetime.now().date()
        )

        conn = get_db()

        ledger_df = pd.read_sql_query("""
            SELECT
                date AS Date,
                voucher_type AS Voucher_Type,
                voucher_no AS Voucher_No,
                particulars AS Particulars,
                debit AS Debit,
                credit AS Credit
            FROM ledger
            WHERE user_mobile=?
            AND account_name=?
            AND date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
        """, conn, params=(
            mob,
            account,
            str(from_date),
            str(to_date)
        ))

        conn.close()

        if ledger_df.empty:

            st.info(
                "📭 या account साठी records उपलब्ध नाहीत."
            )

        else:

            ledger_df["Debit"] = (
                ledger_df["Debit"]
                .fillna(0)
            )

            ledger_df["Credit"] = (
                ledger_df["Credit"]
                .fillna(0)
            )

            ledger_df["Balance"] = (
                ledger_df["Debit"].cumsum()
                - ledger_df["Credit"].cumsum()
            )

            st.dataframe(
                ledger_df,
                use_container_width=True,
                hide_index=True
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total Debit",
                money(ledger_df["Debit"].sum())
            )

            c2.metric(
                "Total Credit",
                money(ledger_df["Credit"].sum())
            )

            c3.metric(
                "Closing Balance",
                money(
                    abs(
                        ledger_df["Balance"].iloc[-1]
                    )
                )
            )


# ============================================================
# PARTY LEDGER
# ============================================================

elif menu == "👥 Party Ledger":

    st.subheader("👥 Party Ledger")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT
            party_name,
            party_type
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:

        st.info(
            "📭 Party Master मध्ये parties उपलब्ध नाहीत."
        )

    else:

        party = st.selectbox(
            "Select Party",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        from_date = c1.date_input(
            "From Date",
            value=datetime.now().date()
        )

        to_date = c2.date_input(
            "To Date",
            value=datetime.now().date()
        )

        conn = get_db()

        party_ledger_df = pd.read_sql_query("""
            SELECT
                date AS Date,
                voucher_type AS Voucher_Type,
                voucher_no AS Voucher_No,
                particulars AS Particulars,
                debit AS Debit,
                credit AS Credit
            FROM ledger
            WHERE user_mobile=?
            AND account_name=?
            AND date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
        """, conn, params=(
            mob,
            party,
            str(from_date),
            str(to_date)
        ))

        conn.close()

        if party_ledger_df.empty:

            st.info(
                "📭 या Party साठी ledger records नाहीत."
            )

        else:

            party_ledger_df["Debit"] = (
                party_ledger_df["Debit"]
                .fillna(0)
            )

            party_ledger_df["Credit"] = (
                party_ledger_df["Credit"]
                .fillna(0)
            )

            party_ledger_df["Balance"] = (
                party_ledger_df["Debit"].cumsum()
                - party_ledger_df["Credit"].cumsum()
            )

            st.dataframe(
                party_ledger_df,
                use_container_width=True,
                hide_index=True
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total Debit",
                money(
                    party_ledger_df["Debit"].sum()
                )
            )

            c2.metric(
                "Total Credit",
                money(
                    party_ledger_df["Credit"].sum()
                )
            )

            c3.metric(
                "Closing Balance",
                money(
                    abs(
                        party_ledger_df[
                            "Balance"
                        ].iloc[-1]
                    )
                )
            )


# ============================================================
# RECEIPT
# ============================================================

elif menu == "💰 Receipt":

    st.subheader("💰 Receipt")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:

        st.warning(
            "⚠️ प्रथम Party Master मध्ये Party तयार करा."
        )

        st.stop()

    with st.form("receipt_form"):

        c1, c2, c3 = st.columns(3)

        receipt_date = c1.date_input(
            "Receipt Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Receipt Voucher No.",
            value="RC-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Received From",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Receipt Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_receipt = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save_receipt:

            if amount <= 0:

                st.error(
                    "❌ Receipt amount 0 पेक्षा जास्त असावी."
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
                    mob,
                    "Receipt",
                    voucher_no,
                    str(receipt_date),
                    party,
                    "",
                    "",
# ============================================================
# RECEIPT
# ============================================================

elif menu == "💰 Receipt":

    st.subheader("💰 Receipt")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:

        st.warning(
            "⚠️ प्रथम Party Master मध्ये Party तयार करा."
        )

        st.stop()

    with st.form("receipt_form"):

        c1, c2, c3 = st.columns(3)

        receipt_date = c1.date_input(
            "Receipt Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Receipt Voucher No.",
            value="RC-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Received From",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Receipt Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_receipt = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save_receipt:

            if amount <= 0:

                st.error(
                    "❌ Receipt amount 0 पेक्षा जास्त असावी."
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
                    mob,
                    "Receipt",
                    voucher_no,
                    str(receipt_date),
                    party,
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    payment_mode,
                    narration,
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
                        balance,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(receipt_date),
                    party,
                    "Customer",
                    "Receipt",
                    voucher_no,
                    narration or "Receipt",
                    0,
                    amount,
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
                    f"✅ Receipt {voucher_no} saved successfully."
                )

                st.metric(
                    "Receipt Amount",
                    money(amount)
                )


# ============================================================
# RECEIPT HISTORY
# ============================================================

elif menu == "📋 Receipt History":

    st.subheader("📋 Receipt History")

    conn = get_db()

    receipt_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Receipt'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if receipt_df.empty:

        st.info(
            "📭 Receipt records उपलब्ध नाहीत."
        )

    else:

        st.dataframe(
            receipt_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Receipt",
            money(
                receipt_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PAYMENT
# ============================================================

elif menu == "💸 Payment":

    st.subheader("💸 Payment")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:

        st.warning(
            "⚠️ प्रथम Party Master मध्ये Supplier तयार करा."
                    )# ============================================================
# RECEIPT
# ============================================================

elif menu == "💰 Receipt":

    st.subheader("💰 Receipt")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:

        st.warning(
            "⚠️ प्रथम Party Master मध्ये Party तयार करा."
        )

        st.stop()

    with st.form("receipt_form"):

        c1, c2, c3 = st.columns(3)

        receipt_date = c1.date_input(
            "Receipt Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Receipt Voucher No.",
            value="RC-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Received From",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Receipt Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_receipt = st.form_submit_button(
            "💾 SAVE RECEIPT"
        )

        if save_receipt:

            if amount <= 0:

                st.error(
                    "❌ Receipt amount 0 पेक्षा जास्त असावी."
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
                    mob,
                    "Receipt",
                    voucher_no,
                    str(receipt_date),
                    party,
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    payment_mode,
                    narration,
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
                        balance,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(receipt_date),
                    party,
                    "Customer",
                    "Receipt",
                    voucher_no,
                    narration or "Receipt",
                    0,
                    amount,
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
                    f"✅ Receipt {voucher_no} saved successfully."
                )

                st.metric(
                    "Receipt Amount",
                    money(amount)
                )


# ============================================================
# RECEIPT HISTORY
# ============================================================

elif menu == "📋 Receipt History":

    st.subheader("📋 Receipt History")

    conn = get_db()

    receipt_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Receipt'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if receipt_df.empty:

        st.info(
            "📭 Receipt records उपलब्ध नाहीत."
        )

    else:

        st.dataframe(
            receipt_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Receipt",
            money(
                receipt_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PAYMENT
# ============================================================

elif menu == "💸 Payment":

    st.subheader("💸 Payment")

    conn = get_db()

    parties_df = pd.read_sql_query("""
        SELECT party_name
        FROM parties
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY party_name
    """, conn, params=(mob,))

    conn.close()

    if parties_df.empty:

        st.warning("First create Supplier in Party Master.")

        st.stop()

    with st.form("payment_form"):

        c1, c2, c3 = st.columns(3)

        payment_date = c1.date_input(
            "Payment Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Payment Voucher No.",
            value="PAY-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        party = c3.selectbox(
            "Paid To",
            parties_df["party_name"].tolist()
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Payment Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_payment = st.form_submit_button(
            "💾 SAVE PAYMENT"
        )

        if save_payment:

            if amount <= 0:

                st.error(
                    "Payment amount must be greater than 0."
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
                    mob,
                    "Payment",
                    voucher_no,
                    str(payment_date),
                    party,
                    "",
                    "",
                    "",
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    amount,
                    payment_mode,
                    narration,
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
                        balance,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(payment_date),
                    party,
                    "Supplier",
                    "Payment",
                    voucher_no,
                    narration or "Payment",
                    amount,
                    0,
                    amount,
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
                    f"Payment {voucher_no} saved successfully."
                )

                st.metric(
                    "Payment Amount",
                    money(amount)
                )


# ============================================================
# PAYMENT HISTORY
# ============================================================

elif menu == "📋 Payment History":

    st.subheader("📋 Payment History")

    conn = get_db()

    payment_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Payment'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if payment_df.empty:

        st.info(
            "No Payment records available."
        )

    else:

        st.dataframe(
            payment_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Payment",
            money(
                payment_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# CASH PAYMENT SUMMARY
# ============================================================

elif menu == "💵 Cash Payment Summary":

    st.subheader("💵 Cash Payment Summary")

    conn = get_db()

    cash_payment_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Payment'
        AND payment_mode='Cash'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if cash_payment_df.empty:

        st.info(
            "No Cash Payment records available."
        )

    else:

        st.dataframe(
            cash_payment_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Cash Payment",
            money(
                cash_payment_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# BANK PAYMENT SUMMARY
# ============================================================

elif menu == "🏦 Bank Payment Summary":

    st.subheader("🏦 Bank Payment Summary")

    conn = get_db()

    bank_payment_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Payment'
        AND payment_mode IN
        (
            'Bank',
            'UPI',
            'Cheque',
            'NEFT',
            'RTGS'
        )
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if bank_payment_df.empty:

        st.info(
            "No Bank Payment records available."
        )

    else:

        st.dataframe(
            bank_payment_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Bank Payment",
            money(
                bank_payment_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# EXPENSE
# ============================================================

elif menu == "💳 Expense":

    st.subheader("💳 Expense")

    with st.form("expense_form"):

        c1, c2, c3 = st.columns(3)

        expense_date = c1.date_input(
            "Expense Date",
            value=datetime.now().date()
        )

        voucher_no = c2.text_input(
            "Expense Voucher No.",
            value="EXP-" + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        expense_head = c3.text_input(
            "Expense Head"
        )

        c1, c2 = st.columns(2)

        amount = c1.number_input(
            "Expense Amount",
            min_value=0.0,
            step=100.0
        )

        payment_mode = c2.selectbox(
            "Payment Mode",
            [
                "Cash",
                "Bank",
                "UPI",
                "Cheque",
                "NEFT",
                "RTGS"
            ]
        )

        narration = st.text_area(
            "Narration"
        )

        save_expense = st.form_submit_button(
            "💾 SAVE EXPENSE"
        )

        if save_expense:

            if not expense_head.strip():

                st.error(
                    "Expense Head is required."
                )

            elif amount <= 0:

                st.error(
                    "Expense amount must be greater than 0."
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
                    mob,
                    "Expense",
                    voucher_no,
                    str(expense_date),
                    expense_head,
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
                    narration,
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
                        balance,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    mob,
                    str(expense_date),
                    expense_head,
                    "Expense",
                    "Expense",
                    voucher_no,
                    narration or expense_head,
                    amount,
                    0,
                    amount,
                    now()
                ))

                conn.commit()
                conn.close()

                log_action(
                    "Expense Created",
                    "Expense",
                    voucher_no
                )

                st.success(
                    f"Expense {voucher_no} saved successfully."
                )

                st.metric(
                    "Expense Amount",
                    money(amount)
                )


# ============================================================
# EXPENSE HISTORY
# ============================================================

elif menu == "📋 Expense History":

    st.subheader("📋 Expense History")

    conn = get_db()

    expense_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Expense_Head,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Expense'
        ORDER BY id DESC
    """, conn, params=(mob,))

    conn.close()

    if expense_df.empty:

        st.info(
            "No Expense records available."
        )

    else:

        st.dataframe(
            expense_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Expense",
            money(
                expense_df["Amount"]
                .fillna(0)
                .sum()
            )
                    )
    # ============================================================
# EXPENSE REPORT
# ============================================================

elif menu == "📊 Expense Report":

    st.subheader("📊 Expense Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    expense_report_df = pd.read_sql_query("""
        SELECT
            party_name AS Expense_Head,
            COUNT(*) AS Transactions,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Expense'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if expense_report_df.empty:

        st.info("No Expense records available.")

    else:

        st.dataframe(
            expense_report_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Expense",
            money(
                expense_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# SALES SUMMARY
# ============================================================

elif menu == "📈 Sales Summary":

    st.subheader("📈 Sales Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_summary_df = pd.read_sql_query("""
        SELECT
            COUNT(*) AS Invoices,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_summary_df.empty:

        st.info("No Sales records available.")

    else:

        row = sales_summary_df.iloc[0]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Invoices",
            int(row["Invoices"])
        )

        c2.metric(
            "Taxable Sales",
            money(row["Taxable"])
        )

        c3.metric(
            "Total Sales",
            money(row["Total"])
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "CGST",
            money(row["CGST"])
        )

        c2.metric(
            "SGST",
            money(row["SGST"])
        )

        c3.metric(
            "IGST",
            money(row["IGST"])
        )


# ============================================================
# PURCHASE SUMMARY
# ============================================================

elif menu == "📉 Purchase Summary":

    st.subheader("📉 Purchase Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_summary_df = pd.read_sql_query("""
        SELECT
            COUNT(*) AS Invoices,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_summary_df.empty:

        st.info("No Purchase records available.")

    else:

        row = purchase_summary_df.iloc[0]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Invoices",
            int(row["Invoices"])
        )

        c2.metric(
            "Taxable Purchase",
            money(row["Taxable"])
        )

        c3.metric(
            "Total Purchase",
            money(row["Total"])
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "CGST",
            money(row["CGST"])
        )

        c2.metric(
            "SGST",
            money(row["SGST"])
        )

        c3.metric(
            "IGST",
            money(row["IGST"])
        )


# ============================================================
# GST SUMMARY
# ============================================================

elif menu == "🧾 GST Summary":

    st.subheader("🧾 GST Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    gst_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(cgst), 0)
                + COALESCE(SUM(sgst), 0)
                + COALESCE(SUM(igst), 0) AS GST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND voucher_type IN
        (
            'Sales',
            'Purchase',
            'Sales Return',
            'Purchase Return'
        )
        GROUP BY voucher_type
        ORDER BY voucher_type
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if gst_df.empty:

        st.info("No GST records available.")

    else:

        st.dataframe(
            gst_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(gst_df["Taxable"].sum())
        )

        c2.metric(
            "Total GST",
            money(gst_df["GST"].sum())
        )

        c3.metric(
            "Total Amount",
            money(gst_df["Total"].sum())
        )


# ============================================================
# GST RATE WISE REPORT
# ============================================================

elif menu == "📊 GST Rate Wise Report":

    st.subheader("📊 GST Rate Wise Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    gst_rate_df = pd.read_sql_query("""
        SELECT
            gst_rate AS GST_Rate,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        GROUP BY gst_rate
        ORDER BY gst_rate
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if gst_rate_df.empty:

        st.info("No GST Rate records available.")

    else:

        st.dataframe(
            gst_rate_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total GST",
            money(
                gst_rate_df["CGST"].sum()
                + gst_rate_df["SGST"].sum()
                + gst_rate_df["IGST"].sum()
            )
        )


# ============================================================
# DAY BOOK
# ============================================================

elif menu == "📖 Day Book":

    st.subheader("📖 Day Book")

    selected_date = st.date_input(
        "Select Date",
        value=datetime.now().date()
    )

    conn = get_db()

    day_book_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode,
            narration AS Narration
        FROM transactions
        WHERE user_mobile=?
        AND date=?
        ORDER BY id ASC
    """, conn, params=(
        mob,
        str(selected_date)
    ))

    conn.close()

    if day_book_df.empty:

        st.info("No transactions available for selected date.")

    else:

        st.dataframe(
            day_book_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Day Total",
            money(
                day_book_df["Amount"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# VOUCHER REGISTER
# ============================================================

elif menu == "📚 Voucher Register":

    st.subheader("📚 Voucher Register")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    voucher_register_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            party_name AS Party,
            total_amount AS Amount,
            payment_mode AS Payment_Mode
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if voucher_register_df.empty:

        st.info("No voucher records available.")

    else:

        st.dataframe(
            voucher_register_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Voucher Amount",
            money(
                voucher_register_df["Amount"]
                .fillna(0)
                .sum()
            )
                    )
    # ============================================================
# SALES REGISTER
# ============================================================

elif menu == "📒 Sales Register":

    st.subheader("📒 Sales Register")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_register_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            item_name AS Item,
            hsn_sac AS HSN_SAC,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            gst_rate AS GST_Rate,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total,
            payment_mode AS Payment_Mode
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_register_df.empty:

        st.info("No Sales records available.")

    else:

        st.dataframe(
            sales_register_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(
                sales_register_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c2.metric(
            "Total GST",
            money(
                sales_register_df["CGST"].fillna(0).sum()
                + sales_register_df["SGST"].fillna(0).sum()
                + sales_register_df["IGST"].fillna(0).sum()
            )
        )

        c3.metric(
            "Total Sales",
            money(
                sales_register_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PURCHASE REGISTER
# ============================================================

elif menu == "📕 Purchase Register":

    st.subheader("📕 Purchase Register")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_register_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            item_name AS Item,
            hsn_sac AS HSN_SAC,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            gst_rate AS GST_Rate,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total,
            payment_mode AS Payment_Mode
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_register_df.empty:

        st.info("No Purchase records available.")

    else:

        st.dataframe(
            purchase_register_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(
                purchase_register_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c2.metric(
            "Total GST",
            money(
                purchase_register_df["CGST"].fillna(0).sum()
                + purchase_register_df["SGST"].fillna(0).sum()
                + purchase_register_df["IGST"].fillna(0).sum()
            )
        )

        c3.metric(
            "Total Purchase",
            money(
                purchase_register_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# SALES RETURN REGISTER
# ============================================================

elif menu == "📗 Sales Return Register":

    st.subheader("📗 Sales Return Register")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_return_register_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            item_name AS Item,
            hsn_sac AS HSN_SAC,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            gst_rate AS GST_Rate,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_return_register_df.empty:

        st.info("No Sales Return records available.")

    else:

        st.dataframe(
            sales_return_register_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(
                sales_return_register_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c2.metric(
            "Total GST",
            money(
                sales_return_register_df["CGST"].fillna(0).sum()
                + sales_return_register_df["SGST"].fillna(0).sum()
                + sales_return_register_df["IGST"].fillna(0).sum()
            )
        )

        c3.metric(
            "Total Sales Return",
            money(
                sales_return_register_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PURCHASE RETURN REGISTER
# ============================================================

elif menu == "📙 Purchase Return Register":

    st.subheader("📙 Purchase Return Register")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_return_register_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            item_name AS Item,
            hsn_sac AS HSN_SAC,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            gst_rate AS GST_Rate,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_return_register_df.empty:

        st.info("No Purchase Return records available.")

    else:

        st.dataframe(
            purchase_return_register_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(
                purchase_return_register_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c2.metric(
            "Total GST",
            money(
                purchase_return_register_df["CGST"].fillna(0).sum()
                + purchase_return_register_df["SGST"].fillna(0).sum()
                + purchase_return_register_df["IGST"].fillna(0).sum()
            )
        )

        c3.metric(
            "Total Purchase Return",
            money(
                purchase_return_register_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# CUSTOMER OUTSTANDING
# ============================================================

elif menu == "👤 Customer Outstanding":

    st.subheader("👤 Customer Outstanding")

    conn = get_db()

    customer_df = pd.read_sql_query("""
        SELECT
            account_name AS Customer,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Customer'
        GROUP BY account_name
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if customer_df.empty:

        st.info("No Customer outstanding records available.")

    else:

        customer_df["Outstanding"] = (
            customer_df["Debit"]
            - customer_df["Credit"]
        )

        customer_df = customer_df[
            customer_df["Outstanding"] > 0
        ].copy()

        st.dataframe(
            customer_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Customer Outstanding",
            money(
                customer_df["Outstanding"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# SUPPLIER OUTSTANDING
# ============================================================

elif menu == "🏢 Supplier Outstanding":

    st.subheader("🏢 Supplier Outstanding")

    conn = get_db()

    supplier_df = pd.read_sql_query("""
        SELECT
            account_name AS Supplier,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Supplier'
        GROUP BY account_name
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if supplier_df.empty:

        st.info("No Supplier outstanding records available.")

    else:

        supplier_df["Outstanding"] = (
            supplier_df["Credit"]
            - supplier_df["Debit"]
        )

        supplier_df = supplier_df[
            supplier_df["Outstanding"] > 0
        ].copy()

        st.dataframe(
            supplier_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Supplier Outstanding",
            money(
                supplier_df["Outstanding"]
                .fillna(0)
                .sum()
            )
                    ) 
     # ============================================================
# CUSTOMER BALANCE
# ============================================================

elif menu == "👤 Customer Balance":

    st.subheader("👤 Customer Balance")

    conn = get_db()

    customer_balance_df = pd.read_sql_query("""
        SELECT
            account_name AS Customer,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Customer'
        GROUP BY account_name
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if customer_balance_df.empty:

        st.info("No Customer balance records available.")

    else:

        customer_balance_df["Balance"] = (
            customer_balance_df["Debit"]
            - customer_balance_df["Credit"]
        )

        st.dataframe(
            customer_balance_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Net Customer Balance",
            money(
                abs(
                    customer_balance_df["Balance"]
                    .fillna(0)
                    .sum()
                )
            )
        )


# ============================================================
# SUPPLIER BALANCE
# ============================================================

elif menu == "🏢 Supplier Balance":

    st.subheader("🏢 Supplier Balance")

    conn = get_db()

    supplier_balance_df = pd.read_sql_query("""
        SELECT
            account_name AS Supplier,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Supplier'
        GROUP BY account_name
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if supplier_balance_df.empty:

        st.info("No Supplier balance records available.")

    else:

        supplier_balance_df["Balance"] = (
            supplier_balance_df["Credit"]
            - supplier_balance_df["Debit"]
        )

        st.dataframe(
            supplier_balance_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Net Supplier Balance",
            money(
                abs(
                    supplier_balance_df["Balance"]
                    .fillna(0)
                    .sum()
                )
            )
        )


# ============================================================
# ITEM STOCK VALUATION
# ============================================================

elif menu == "📦 Item Stock Valuation":

    st.subheader("📦 Item Stock Valuation")

    conn = get_db()

    stock_valuation_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            current_stock AS Quantity,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if stock_valuation_df.empty:

        st.info("No stock records available.")

    else:

        stock_valuation_df["Quantity"] = (
            stock_valuation_df["Quantity"]
            .fillna(0)
        )

        stock_valuation_df["Purchase_Rate"] = (
            stock_valuation_df["Purchase_Rate"]
            .fillna(0)
        )

        stock_valuation_df["Sale_Rate"] = (
            stock_valuation_df["Sale_Rate"]
            .fillna(0)
        )

        stock_valuation_df["Purchase_Value"] = (
            stock_valuation_df["Quantity"]
            * stock_valuation_df["Purchase_Rate"]
        )

        stock_valuation_df["Sale_Value"] = (
            stock_valuation_df["Quantity"]
            * stock_valuation_df["Sale_Rate"]
        )

        st.dataframe(
            stock_valuation_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Purchase Stock Value",
            money(
                stock_valuation_df["Purchase_Value"]
                .sum()
            )
        )

        c2.metric(
            "Sale Stock Value",
            money(
                stock_valuation_df["Sale_Value"]
                .sum()
            )
        )


# ============================================================
# PROFIT AND LOSS
# ============================================================

elif menu == "📊 Profit & Loss":

    st.subheader("📊 Profit & Loss")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS Total_Sales
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    purchase_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS Total_Purchase
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    expense_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS Total_Expense
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Expense'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    sales_return_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS Total_Sales_Return
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    purchase_return_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS Total_Purchase_Return
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        AND date BETWEEN ? AND ?
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    total_sales = float(
        sales_df.iloc[0]["Total_Sales"]
    )

    total_purchase = float(
        purchase_df.iloc[0]["Total_Purchase"]
    )

    total_expense = float(
        expense_df.iloc[0]["Total_Expense"]
    )

    total_sales_return = float(
        sales_return_df.iloc[0]["Total_Sales_Return"]
    )

    total_purchase_return = float(
        purchase_return_df.iloc[0]["Total_Purchase_Return"]
    )

    net_sales = (
        total_sales
        - total_sales_return
    )

    net_purchase = (
        total_purchase
        - total_purchase_return
    )

    gross_profit = (
        net_sales
        - net_purchase
    )

    net_profit = (
        gross_profit
        - total_expense
    )

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
        "Gross Profit",
        money(gross_profit)
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Expense",
        money(total_expense)
    )

    c2.metric(
        "Net Profit",
        money(net_profit)
    )

    c3.metric(
        "Sales Return",
        money(total_sales_return)
    )

    st.dataframe(
        pd.DataFrame({
            "Particulars": [
                "Sales",
                "Sales Return",
                "Net Sales",
                "Purchase",
                "Purchase Return",
                "Net Purchase",
                "Gross Profit",
                "Expense",
                "Net Profit"
            ],
            "Amount": [
                total_sales,
                total_sales_return,
                net_sales,
                total_purchase,
                total_purchase_return,
                net_purchase,
                gross_profit,
                total_expense,
                net_profit
            ]
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BALANCE SHEET
# ============================================================

elif menu == "📑 Balance Sheet":

    st.subheader("📑 Balance Sheet")

    conn = get_db()

    asset_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type IN
        (
            'Customer',
            'Cash',
            'Bank',
            'Asset'
        )
    """, conn, params=(mob,))

    liability_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type IN
        (
            'Supplier',
            'Liability'
        )
    """, conn, params=(mob,))

    expense_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(debit), 
     # ============================================================
# BALANCE SHEET
# ============================================================

elif menu == "📑 Balance Sheet":

    st.subheader("📑 Balance Sheet")

    conn = get_db()

    asset_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type IN
        (
            'Customer',
            'Cash',
            'Bank',
            'Asset'
        )
    """, conn, params=(mob,))

    liability_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type IN
        (
            'Supplier',
            'Liability'
        )
    """, conn, params=(mob,))

    expense_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(debit), 0) AS Debit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Expense'
    """, conn, params=(mob,))

    income_df = pd.read_sql_query("""
        SELECT
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Income'
    """, conn, params=(mob,))

    conn.close()

    total_assets = (
        float(asset_df.iloc[0]["Debit"])
        - float(asset_df.iloc[0]["Credit"])
    )

    total_liabilities = (
        float(liability_df.iloc[0]["Credit"])
        - float(liability_df.iloc[0]["Debit"])
    )

    total_expenses = float(
        expense_df.iloc[0]["Debit"]
    )

    total_income = float(
        income_df.iloc[0]["Credit"]
    )

    net_profit = (
        total_income
        - total_expenses
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "Total Assets",
        money(abs(total_assets))
    )

    c2.metric(
        "Total Liabilities",
        money(abs(total_liabilities))
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "Total Income",
        money(total_income)
    )

    c2.metric(
        "Total Expenses",
        money(total_expenses)
    )

    st.metric(
        "Net Profit / Loss",
        money(abs(net_profit))
    )

    balance_sheet_df = pd.DataFrame({
        "Particulars": [
            "Total Assets",
            "Total Liabilities",
            "Total Income",
            "Total Expenses",
            "Net Profit / Loss"
        ],
        "Amount": [
            abs(total_assets),
            abs(total_liabilities),
            total_income,
            total_expenses,
            abs(net_profit)
        ]
    })

    st.dataframe(
        balance_sheet_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TRIAL BALANCE
# ============================================================

elif menu == "⚖️ Trial Balance":

    st.subheader("⚖️ Trial Balance")

    conn = get_db()

    trial_balance_df = pd.read_sql_query("""
        SELECT
            account_name AS Account,
            account_type AS Account_Type,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit
        FROM ledger
        WHERE user_mobile=?
        GROUP BY account_name, account_type
        ORDER BY account_name
    """, conn, params=(mob,))

    conn.close()

    if trial_balance_df.empty:

        st.info("No Trial Balance records available.")

    else:

        trial_balance_df["Debit"] = (
            trial_balance_df["Debit"].fillna(0)
        )

        trial_balance_df["Credit"] = (
            trial_balance_df["Credit"].fillna(0)
        )

        st.dataframe(
            trial_balance_df,
            use_container_width=True,
            hide_index=True
        )

        total_debit = trial_balance_df["Debit"].sum()
        total_credit = trial_balance_df["Credit"].sum()

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Debit",
            money(total_debit)
        )

        c2.metric(
            "Total Credit",
            money(total_credit)
        )

        difference = total_debit - total_credit

        if abs(difference) < 0.01:
            st.success("Trial Balance is Balanced.")
        else:
            st.warning(
                f"Trial Balance Difference: {money(abs(difference))}"
            )


# ============================================================
# GST RETURN SUMMARY
# ============================================================

elif menu == "🧾 GST Return Summary":

    st.subheader("🧾 GST Return Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    gst_return_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            COUNT(*) AS Transactions,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(cgst), 0)
                + COALESCE(SUM(sgst), 0)
                + COALESCE(SUM(igst), 0) AS Total_GST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        AND voucher_type IN
        (
            'Sales',
            'Purchase',
            'Sales Return',
            'Purchase Return'
        )
        GROUP BY voucher_type
        ORDER BY voucher_type
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if gst_return_df.empty:

        st.info("No GST Return records available.")

    else:

        st.dataframe(
            gst_return_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Taxable Amount",
            money(
                gst_return_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c2.metric(
            "Total GST",
            money(
                gst_return_df["Total_GST"]
                .fillna(0)
                .sum()
            )
        )

        c3.metric(
            "Total Amount",
            money(
                gst_return_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# CASH BOOK
# ============================================================

elif menu == "💵 Cash Book":

    st.subheader("💵 Cash Book")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    cash_book_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            account_name AS Account,
            particulars AS Particulars,
            debit AS Debit,
            credit AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Cash'
        AND date BETWEEN ? AND ?
        ORDER BY date ASC, id ASC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if cash_book_df.empty:

        st.info("No Cash Book records available.")

    else:

        cash_book_df["Debit"] = (
            cash_book_df["Debit"].fillna(0)
        )

        cash_book_df["Credit"] = (
            cash_book_df["Credit"].fillna(0)
        )

        cash_book_df["Balance"] = (
            cash_book_df["Debit"].cumsum()
            - cash_book_df["Credit"].cumsum()
        )

        st.dataframe(
            cash_book_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Debit",
            money(cash_book_df["Debit"].sum())
        )

        c2.metric(
            "Total Credit",
            money(cash_book_df["Credit"].sum())
        )

        c3.metric(
            "Closing Balance",
            money(
                abs(
                    cash_book_df["Balance"].iloc[-1]
                )
            )
        )


# ============================================================
# BANK BOOK
# ============================================================

elif menu == "🏦 Bank Book":

    st.subheader("🏦 Bank Book")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    bank_book_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            account_name AS Account,
            particulars AS Particulars,
            debit AS Debit,
            credit AS Credit
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Bank'
        AND date BETWEEN ? AND ?
        ORDER BY date ASC, id ASC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if bank_book_df.empty:

        st.info("No Bank Book records available.")

    else:

        bank_book_df["Debit"] = (
            bank_book_df["Debit"].fillna(0)
        )

        bank_book_df["Credit"] = (
            bank_book_df["Credit"].fillna(0)
        )

        bank_book_df["Balance"] = (
            bank_book_df["Debit"].cumsum()
            - bank_book_df["Credit"].cumsum()
        )

        st.dataframe(
            bank_book_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Debit",
            money(bank_book_df["Debit"].sum())
        )

        c2.metric(
            "Total Credit",
            money(bank_book_df["Credit"].sum())
        )

        c3.metric(
            "Closing Balance",
            money(
                abs(
                    bank_book_df["Balance"].iloc[-1]
                )
            )
        )


# ============================================================
# TRANSACTION REPORT
# ============================================================

elif menu == "📋 Transaction Report":

    st.subheader("📋 Transaction Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    transaction_report_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            party_name AS Party,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            taxable_amount AS Taxable,
            gst_rate AS GST_Rate,
            total_amount AS Total,
            payment_mode AS Payment_Mode
        FROM transactions
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if transaction_report_df.empty:

        st.info("No Transaction records available.")

    else:

        st.dataframe(
            transaction_report_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Transaction Amount",
            money(
                transaction_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# ITEM WISE SALES
# ============================================================

elif menu == "📦 Item Wise Sales":

    st.subheader("📦 Item Wise Sales")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    item_sales_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            SUM(qty) AS Quantity,
            COALESCE(AVG(rate), 0) AS Average_Rate,
            COALESCE(SUM(discount), 0) AS Discount,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY item_name, unit
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if item_sales_df.empty:

        st.info("No Item Wise Sales records available.")

    else:

        st.dataframe(
            item_sales_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Items",
            len(item_sales_df)
        )

        c2.metric(
            "Total Quantity",
            item_sales_df["Quantity"]
            .fillna(0)
            .sum()
        )

        c3.metric(
            "Total Sales",
            money(
                item_sales_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# ITEM WISE PURCHASE
# ============================================================

elif menu == "📦 Item Wise Purchase":

    st.subheader("📦 Item Wise Purchase")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    item_purchase_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            SUM(qty) AS Quantity,
            COALESCE(AVG(rate), 0) AS Average_Rate,
            COALESCE(SUM(discount), 0) AS Discount,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        GROUP BY item_name, unit
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if item_purchase_df.empty:

        st.info("No Item Wise Purchase records available.")

    else:

        st.dataframe(
            item_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Items",
            len(item_purchase_df)
        )

        c2.metric(
            "Total Quantity",
            item_purchase_df["Quantity"]
            .fillna(0)
            .sum()
        )

        c3.metric(
            "Total Purchase",
            money(
                item_purchase_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# STOCK SUMMARY
# ============================================================

elif menu == "📦 Stock Summary":

    st.subheader("📦 Stock Summary")

    conn = get_db()

    stock_summary_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            hsn_sac AS HSN_SAC,
            gst_rate AS GST_Rate,
            current_stock AS Current_Stock,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if stock_summary_df.empty:

        st.info("No Stock records available.")

    else:

        stock_summary_df["Current_Stock"] = (
            stock_summary_df["Current_Stock"].fillna(0)
        )

        stock_summary_df["Purchase_Rate"] = (
            stock_summary_df["Purchase_Rate"].fillna(0)
        )

        stock_summary_df["Sale_Rate"] = (
            stock_summary_df["Sale_Rate"].fillna(0)
        )

        stock_summary_df["Purchase_Value"] = (
            stock_summary_df["Current_Stock"]
            * stock_summary_df["Purchase_Rate"]
        )

        stock_summary_df["Sale_Value"] = (
            stock_summary_df["Current_Stock"]
            * stock_summary_df["Sale_Rate"]
        )

        st.dataframe(
            stock_summary_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Items",
            len(stock_summary_df)
        )

        c2.metric(
            "Total Stock Quantity",
            stock_summary_df["Current_Stock"].sum()
        )

        c3.metric(
            "Stock Value",
            money(
                stock_summary_df["Purchase_Value"].sum()
            )
        )


# ============================================================
# LOW STOCK REPORT
# ============================================================

elif menu == "⚠️ Low Stock Report":

    st.subheader("⚠️ Low Stock Report")

    conn = get_db()

    low_stock_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            current_stock AS Current_Stock,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        AND COALESCE(current_stock, 0) <= 5
        ORDER BY current_stock ASC, item_name
    """, conn, params=(mob,))

    conn.close()

    if low_stock_df.empty:

        st.success("No Low Stock items found.")

    else:

        st.dataframe(
            low_stock_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Low Stock Items",
            len(low_stock_df)
        )


# ============================================================
# OUT OF STOCK REPORT
# ============================================================

elif menu == "🚫 Out of Stock":

    st.subheader("🚫 Out of Stock")

    conn = get_db()

    out_of_stock_df = pd.read_sql_query("""
        SELECT
            item_name AS Item,
            unit AS Unit,
            hsn_sac AS HSN_SAC,
            gst_rate AS GST_Rate,
            current_stock AS Current_Stock,
            purchase_price AS Purchase_Rate,
            sale_price AS Sale_Rate
        FROM items
        WHERE user_mobile=?
        AND is_active=1
        AND COALESCE(current_stock, 0) <= 0
        ORDER BY item_name
    """, conn, params=(mob,))

    conn.close()

    if out_of_stock_df.empty:

        st.success("No Out of Stock items found.")

    else:

        st.dataframe(
            out_of_stock_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Out of Stock Items",
            len(out_of_stock_df)
        )


# ============================================================
# STOCK MOVEMENT REPORT
# ============================================================

elif menu == "📦 Stock Movement Report":

    st.subheader("📦 Stock Movement Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    stock_movement_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            item_name AS Item,
            godown AS Godown,
            movement_type AS Movement_Type,
            reference_no AS Reference_No,
            qty_in AS Qty_In,
            qty_out AS Qty_Out,
            balance_qty AS Balance_Qty,
            rate AS Rate
        FROM stock_movements
        WHERE user_mobile=?
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if stock_movement_df.empty:

        st.info("No Stock Movement records available.")

    else:

        st.dataframe(
            stock_movement_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Qty In",
            stock_movement_df["Qty_In"]
            .fillna(0)
            .sum()
        )

        c2.metric(
            "Total Qty Out",
            stock_movement_df["Qty_Out"]
            .fillna(0)
            .sum()
                    ) 
    # ============================================================
# EXPENSE REPORT
# ============================================================

elif menu == "💸 Expense Report":

    st.subheader("💸 Expense Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    expense_report_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Party,
            narration AS Particulars,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total,
            payment_mode AS Payment_Mode
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Expense'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if expense_report_df.empty:

        st.info("No Expense records available.")

    else:

        st.dataframe(
            expense_report_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Expense",
            money(
                expense_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )

        c2.metric(
            "Total Transactions",
            len(expense_report_df)
        )


# ============================================================
# GST INPUT CREDIT
# ============================================================

elif menu == "🧾 GST Input Credit":

    st.subheader("🧾 GST Input Credit")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    input_gst_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            date AS Date,
            party_name AS Party,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type IN
        (
            'Purchase',
            'Purchase Return'
        )
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if input_gst_df.empty:

        st.info("No GST Input Credit records available.")

    else:

        st.dataframe(
            input_gst_df,
            use_container_width=True,
            hide_index=True
        )

        input_cgst = input_gst_df["CGST"].fillna(0).sum()
        input_sgst = input_gst_df["SGST"].fillna(0).sum()
        input_igst = input_gst_df["IGST"].fillna(0).sum()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Input CGST",
            money(input_cgst)
        )

        c2.metric(
            "Input SGST",
            money(input_sgst)
        )

        c3.metric(
            "Input IGST",
            money(input_igst)
        )

        st.metric(
            "Total Input GST",
            money(
                input_cgst
                + input_sgst
                + input_igst
            )
        )


# ============================================================
# GST OUTPUT LIABILITY
# ============================================================

elif menu == "🧾 GST Output Liability":

    st.subheader("🧾 GST Output Liability")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    output_gst_df = pd.read_sql_query("""
        SELECT
            voucher_type AS Voucher_Type,
            voucher_no AS Voucher_No,
            date AS Date,
            party_name AS Party,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type IN
        (
            'Sales',
            'Sales Return'
        )
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if output_gst_df.empty:

        st.info("No GST Output Liability records available.")

    else:

        st.dataframe(
            output_gst_df,
            use_container_width=True,
            hide_index=True
        )

        output_cgst = output_gst_df["CGST"].fillna(0).sum()
        output_sgst = output_gst_df["SGST"].fillna(0).sum()
        output_igst = output_gst_df["IGST"].fillna(0).sum()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Output CGST",
            money(output_cgst)
        )

        c2.metric(
            "Output SGST",
            money(output_sgst)
        )

        c3.metric(
            "Output IGST",
            money(output_igst)
        )

        st.metric(
            "Total Output GST",
            money(
                output_cgst
                + output_sgst
                + output_igst
            )
        )


# ============================================================
# HSN SUMMARY
# ============================================================

elif menu == "📋 HSN Summary":

    st.subheader("📋 HSN Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    hsn_df = pd.read_sql_query("""
        SELECT
            hsn_sac AS HSN_SAC,
            item_name AS Item,
            gst_rate AS GST_Rate,
            SUM(qty) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY hsn_sac, item_name, gst_rate
        ORDER BY hsn_sac, item_name
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if hsn_df.empty:

        st.info("No HSN Summary records available.")

    else:

        st.dataframe(
            hsn_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Taxable",
            money(hsn_df["Taxable"].sum())
        )

        c2.metric(
            "Total GST",
            money(
                hsn_df["CGST"].sum()
                + hsn_df["SGST"].sum()
                + hsn_df["IGST"].sum()
            )
        )

        c3.metric(
            "Total Amount",
            money(hsn_df["Total"].sum())
        )


# ============================================================
# DAILY SALES SUMMARY
# ============================================================

elif menu == "📅 Daily Sales Summary":

    st.subheader("📅 Daily Sales Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    daily_sales_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if daily_sales_df.empty:

        st.info("No Daily Sales records available.")

    else:

        st.dataframe(
            daily_sales_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Sales",
            money(
                daily_sales_df["Total"]
                .fillna(0)
                .sum()
            )
                    if# ============================================================
# DAILY PURCHASE SUMMARY
# ============================================================

elif menu == "📅 Daily Purchase Summary":

    st.subheader("📅 Daily Purchase Summary")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    daily_purchase_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if daily_purchase_df.empty:

        st.info("No Daily Purchase records available.")

    else:

        st.dataframe(
            daily_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        total_purchase = (
            daily_purchase_df["Total"]
            .fillna(0)
            .sum()
        )

        st.metric(
            "Total Purchase",
            money(total_purchase)
                )

# ============================================================
# MONTHLY SALES SUMMARY
# ============================================================

elif menu == "📊 Monthly Sales Summary":

    st.subheader("📊 Monthly Sales Summary")

    conn = get_db()

    monthly_sales_df = pd.read_sql_query("""
        SELECT
            strftime('%Y-%m', date) AS Month,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        GROUP BY strftime('%Y-%m', date)
        ORDER BY Month DESC
    """, conn, params=(mob,))

    conn.close()

    if monthly_sales_df.empty:

        st.info("No Monthly Sales records available.")

    else:

        st.dataframe(
            monthly_sales_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Sales",
            money(
                monthly_sales_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# MONTHLY PURCHASE SUMMARY
# ============================================================

elif menu == "📊 Monthly Purchase Summary":

    st.subheader("📊 Monthly Purchase Summary")

    conn = get_db()

    monthly_purchase_df = pd.read_sql_query("""
        SELECT
            strftime('%Y-%m', date) AS Month,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        GROUP BY strftime('%Y-%m', date)
        ORDER BY Month DESC
    """, conn, params=(mob,))

    conn.close()

    if monthly_purchase_df.empty:

        st.info("No Monthly Purchase records available.")

    else:

        st.dataframe(
            monthly_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Purchase",
            money(
                monthly_purchase_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# SALES RETURN REPORT
# ============================================================

elif menu == "📋 Sales Return Report":

    st.subheader("📋 Sales Return Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_return_report_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_return_report_df.empty:

        st.info("No Sales Return records available.")

    else:

        st.dataframe(
            sales_return_report_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Quantity",
            sales_return_report_df["Quantity"]
            .fillna(0)
            .sum()
        )

        c2.metric(
            "Total Taxable",
            money(
                sales_return_report_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c3.metric(
            "Total Return",
            money(
                sales_return_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PURCHASE RETURN REPORT
# ============================================================

elif menu == "📋 Purchase Return Report":

    st.subheader("📋 Purchase Return Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_return_report_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_return_report_df.empty:

        st.info("No Purchase Return records available.")

    else:

        st.dataframe(
            purchase_return_report_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Quantity",
            purchase_return_report_df["Quantity"]
            .fillna(0)
            .sum()
        )

        c2.metric(
            "Total Taxable",
            money(
                purchase_return_report_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c3.metric(
            "Total Return",
            money(
                purchase_return_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PARTY WISE SALES
# ============================================================

elif menu == "👥 Party Wise Sales":

    st.subheader("👥 Party Wise Sales")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    party_sales_df = pd.read_sql_query("""
        SELECT
            party_name AS Party,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if party_sales_df.empty:

        st.info("No Party Wise Sales records available.")

    else:

        st.dataframe(
            party_sales_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Parties",
            len(party_sales_df)
        )

        c2.metric(
            "Total Sales",
            money(
                party_sales_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PARTY WISE PURCHASE
# ============================================================

elif menu == "👥 Party Wise Purchase":

    st.subheader("👥 Party Wise Purchase")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    party_purchase_df = pd.read_sql_query("""
        SELECT
            party_name AS Party,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if party_purchase_df.empty:

        st.info("No Party Wise Purchase records available.")

    else:

        st.dataframe(
            party_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Parties",
            len(party_purchase_df)
        )

        c2.metric(
            "Total Purchase",
            money(
                party_purchase_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# CUSTOMER OUTSTANDING
# ============================================================

elif menu == "💰 Customer Outstanding":

    st.subheader("💰 Customer Outstanding")

    conn = get_db()

    customer_outstanding_df = pd.read_sql_query("""
        SELECT
            account_name AS Customer,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit,
            COALESCE(SUM(debit), 0)
                - COALESCE(SUM(credit), 0) AS Outstanding
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Customer'
        GROUP BY account_name
        HAVING Outstanding > 0
        ORDER BY Outstanding DESC
    """, conn, params=(mob,))

    conn.close()

    if customer_outstanding_df.empty:

        st.success("No Customer Outstanding records available.")

    else:

        st.dataframe(
            customer_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Customer Outstanding",
            money(
                customer_outstanding_df["Outstanding"]
                .sum()
            )
        )


# ============================================================
# SUPPLIER OUTSTANDING
# ============================================================

elif menu == "💳 Supplier Outstanding":

    st.subheader("💳 Supplier Outstanding")

    conn = get_db()

    supplier_outstanding_df = pd.read_sql_query("""
        SELECT
            account_name AS Supplier,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit,
            COALESCE(SUM(credit), 0)
                - COALESCE(SUM(debit), 0) AS Outstanding
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Supplier'
        GROUP BY account_name
        HAVING Outstanding > 0
        ORDER BY Outstanding DESC
    """, conn, params=(mob,))

    conn.close()

    if supplier_outstanding_df.empty:

        st.success("No Supplier Outstanding records available.")

    else:

        st.dataframe(
            supplier_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Supplier Outstanding",
            money(
                supplier_outstanding_df["Outstanding"]
                .sum()
            )
                )# ============================================================
# SALES RETURN REPORT
# ============================================================

elif menu == "📋 Sales Return Report":

    st.subheader("📋 Sales Return Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    sales_return_report_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Customer,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if sales_return_report_df.empty:

        st.info("No Sales Return records available.")

    else:

        st.dataframe(
            sales_return_report_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Quantity",
            sales_return_report_df["Quantity"]
            .fillna(0)
            .sum()
        )

        c2.metric(
            "Total Taxable",
            money(
                sales_return_report_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c3.metric(
            "Total Return",
            money(
                sales_return_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PURCHASE RETURN REPORT
# ============================================================

elif menu == "📋 Purchase Return Report":

    st.subheader("📋 Purchase Return Report")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    purchase_return_report_df = pd.read_sql_query("""
        SELECT
            date AS Date,
            voucher_no AS Voucher_No,
            party_name AS Supplier,
            item_name AS Item,
            qty AS Quantity,
            rate AS Rate,
            discount AS Discount,
            taxable_amount AS Taxable,
            cgst AS CGST,
            sgst AS SGST,
            igst AS IGST,
            total_amount AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase Return'
        AND date BETWEEN ? AND ?
        ORDER BY date DESC, id DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if purchase_return_report_df.empty:

        st.info("No Purchase Return records available.")

    else:

        st.dataframe(
            purchase_return_report_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Quantity",
            purchase_return_report_df["Quantity"]
            .fillna(0)
            .sum()
        )

        c2.metric(
            "Total Taxable",
            money(
                purchase_return_report_df["Taxable"]
                .fillna(0)
                .sum()
            )
        )

        c3.metric(
            "Total Return",
            money(
                purchase_return_report_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PARTY WISE SALES
# ============================================================

elif menu == "👥 Party Wise Sales":

    st.subheader("👥 Party Wise Sales")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    party_sales_df = pd.read_sql_query("""
        SELECT
            party_name AS Party,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Sales'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if party_sales_df.empty:

        st.info("No Party Wise Sales records available.")

    else:

        st.dataframe(
            party_sales_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Parties",
            len(party_sales_df)
        )

        c2.metric(
            "Total Sales",
            money(
                party_sales_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# PARTY WISE PURCHASE
# ============================================================

elif menu == "👥 Party Wise Purchase":

    st.subheader("👥 Party Wise Purchase")

    c1, c2 = st.columns(2)

    from_date = c1.date_input(
        "From Date",
        value=datetime.now().date()
    )

    to_date = c2.date_input(
        "To Date",
        value=datetime.now().date()
    )

    conn = get_db()

    party_purchase_df = pd.read_sql_query("""
        SELECT
            party_name AS Party,
            COUNT(*) AS Transactions,
            COALESCE(SUM(qty), 0) AS Quantity,
            COALESCE(SUM(taxable_amount), 0) AS Taxable,
            COALESCE(SUM(cgst), 0) AS CGST,
            COALESCE(SUM(sgst), 0) AS SGST,
            COALESCE(SUM(igst), 0) AS IGST,
            COALESCE(SUM(total_amount), 0) AS Total
        FROM transactions
        WHERE user_mobile=?
        AND voucher_type='Purchase'
        AND date BETWEEN ? AND ?
        GROUP BY party_name
        ORDER BY Total DESC
    """, conn, params=(
        mob,
        str(from_date),
        str(to_date)
    ))

    conn.close()

    if party_purchase_df.empty:

        st.info("No Party Wise Purchase records available.")

    else:

        st.dataframe(
            party_purchase_df,
            use_container_width=True,
            hide_index=True
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Parties",
            len(party_purchase_df)
        )

        c2.metric(
            "Total Purchase",
            money(
                party_purchase_df["Total"]
                .fillna(0)
                .sum()
            )
        )


# ============================================================
# CUSTOMER OUTSTANDING
# ============================================================

elif menu == "💰 Customer Outstanding":

    st.subheader("💰 Customer Outstanding")

    conn = get_db()

    customer_outstanding_df = pd.read_sql_query("""
        SELECT
            account_name AS Customer,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit,
            COALESCE(SUM(debit), 0)
                - COALESCE(SUM(credit), 0) AS Outstanding
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Customer'
        GROUP BY account_name
        HAVING Outstanding > 0
        ORDER BY Outstanding DESC
    """, conn, params=(mob,))

    conn.close()

    if customer_outstanding_df.empty:

        st.success("No Customer Outstanding records available.")

    else:

        st.dataframe(
            customer_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Customer Outstanding",
            money(
                customer_outstanding_df["Outstanding"]
                .sum()
            )
        )


# ============================================================
# SUPPLIER OUTSTANDING
# ============================================================

elif menu == "💳 Supplier Outstanding":

    st.subheader("💳 Supplier Outstanding")

    conn = get_db()

    supplier_outstanding_df = pd.read_sql_query(
        """
        SELECT
            account_name AS Supplier,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit,
            (
                COALESCE(SUM(credit), 0)
                - COALESCE(SUM(debit), 0)
            ) AS Outstanding
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Supplier'
        GROUP BY account_name
        HAVING Outstanding > 0
        ORDER BY Outstanding DESC
        """,
        conn,
        params=(mob,)
    )

    conn.close()

    if supplier_outstanding_df.empty:

        st.success("No Supplier Outstanding records available.")

    else:

        st.dataframe(
            supplier_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        total_supplier_outstanding = (
            supplier_outstanding_df["Outstanding"]
            .fillna(0)
            .sum()
        )

        st.metric(
            "Total Supplier Outstanding",
            money(total_supplier_outstanding)
        )


# ============================================================
# CUSTOMER OUTSTANDING SUMMARY
# ============================================================

elif menu == "💰 Customer Outstanding Summary":

    st.subheader("💰 Customer Outstanding Summary")

    conn = get_db()

    customer_outstanding_df = pd.read_sql_query(
        """
        SELECT
            account_name AS Customer,
            COALESCE(SUM(debit), 0) AS Debit,
            COALESCE(SUM(credit), 0) AS Credit,
            (
                COALESCE(SUM(debit), 0)
                - COALESCE(SUM(credit), 0)
            ) AS Outstanding
        FROM ledger
        WHERE user_mobile=?
        AND account_type='Customer'
        GROUP BY account_name
        HAVING Outstanding > 0
        ORDER BY Outstanding DESC
        """,
        conn,
        params=(mob,)
    )

    conn.close()

    if customer_outstanding_df.empty:

        st.success("No Customer Outstanding records available.")

    else:

        st.dataframe(
            customer_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        total_customer_outstanding = (
            customer_outstanding_df["Outstanding"]
            .fillna(0)
            .sum()
        )

        st.metric(
            "Total Customer Outstanding",
            money(total_customer_outstanding)
    )
# ============================================================
# SUPPLIER OUTSTANDING
# ============================================================

elif menu == "💳 Supplier Outstanding":

    st.subheader("💳 Supplier Outstanding")

    conn = get_db()

    supplier_outstanding_df = pd.read_sql_query(
        "SELECT account_name AS Supplier, "
        "COALESCE(SUM(debit), 0) AS Debit, "
        "COALESCE(SUM(credit), 0) AS Credit, "
        "(COALESCE(SUM(credit), 0) - "
        "COALESCE(SUM(debit), 0)) AS Outstanding "
        "FROM ledger "
        "WHERE user_mobile=? "
        "AND account_type='Supplier' "
        "GROUP BY account_name "
        "HAVING Outstanding > 0 "
        "ORDER BY Outstanding DESC",
        conn,
        params=(mob,)
    )

    conn.close()

    if supplier_outstanding_df.empty:

        st.success("No Supplier Outstanding records available.")

    else:

        st.dataframe(
            supplier_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        total_outstanding = (
            supplier_outstanding_df["Outstanding"]
            .fillna(0)
            .sum()
        )

        st.metric(
            "Total Supplier Outstanding",
            money(total_outstanding)
        )


# ============================================================
# CUSTOMER OUTSTANDING SUMMARY
# ============================================================

elif menu == "💰 Customer Outstanding Summary":

    st.subheader("💰 Customer Outstanding Summary")

    conn = get_db()

    customer_outstanding_df = pd.read_sql_query(
        "SELECT account_name AS Customer, "
        "COALESCE(SUM(debit), 0) AS Debit, "
        "COALESCE(SUM(credit), 0) AS Credit, "
        "(COALESCE(SUM(debit), 0) - "
        "COALESCE(SUM(credit), 0)) AS Outstanding "
        "FROM ledger "
        "WHERE user_mobile=? "
        "AND account_type='Customer' "
        "GROUP BY account_name "
        "HAVING Outstanding > 0 "
        "ORDER BY Outstanding DESC",
        conn,
        params=(mob,)
    )

    conn.close()

    if customer_outstanding_df.empty:

        st.success("No Customer Outstanding records available.")

    else:

        st.dataframe(
            customer_outstanding_df,
            use_container_width=True,
            hide_index=True
        )

        total_outstanding = (
            customer_outstanding_df["Outstanding"]
            .fillna(0)
            .sum()
        )

        st.metric(
            "Total Customer Outstanding",
            money(total_outstanding)
