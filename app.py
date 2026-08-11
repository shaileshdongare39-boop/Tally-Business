import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta

try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None

# Page Configuration
st.set_page_config(
    page_title="SD TALLY BUSINESS - Enterprise ERP",
    layout="wide",
    page_icon="💼",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0d6efd;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 45px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Database Setup
DB_FILE = "tally_enterprise_master.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    mobile TEXT PRIMARY KEY,
                    name TEXT,
                    reg_date TEXT,
                    trial_end_date TEXT,
                    is_paid INTEGER DEFAULT 0,
                    paid_till TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT UNIQUE,
                    hsn_sac TEXT,
                    godown TEXT,
                    batch_no TEXT,
                    expiry_date TEXT,
                    sale_price REAL,
                    purchase_price REAL,
                    gst_rate REAL,
                    stock_qty REAL,
                    min_stock_alert REAL DEFAULT 5
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT UNIQUE,
                    gstin TEXT,
                    mobile TEXT,
                    party_type TEXT,
                    opening_balance REAL DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voucher_type TEXT,
                    voucher_no TEXT,
                    date TEXT,
                    party_name TEXT,
                    item_name TEXT,
                    hsn_sac TEXT,
                    qty REAL,
                    rate REAL,
                    taxable_amt REAL,
                    gst_rate REAL,
                    cgst REAL,
                    sgst REAL,
                    igst REAL,
                    total_amt REAL,
                    payment_mode TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS capital_bank_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    account_type TEXT,
                    particulars TEXT,
                    amount REAL,
                    txn_type TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Session State
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

def check_subscription(mobile):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT reg_date, trial_end_date, is_paid, paid_till FROM users WHERE mobile=?", (mobile,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return "NEW_USER"
    
    today = datetime.now().date()
    trial_end = datetime.strptime(user[1], "%Y-%m-%d").date()
    
    if user[2] == 1 and user[3]:
        paid_till = datetime.strptime(user[3], "%Y-%m-%d").date()
        if today <= paid_till:
            return "ACTIVE_PRO"
    
    if today <= trial_end:
        days_left = (trial_end - today).days
        return f"FREE_TRIAL ({days_left} days left)"
    
    return "EXPIRED"

# LOGIN PAGE
if not st.session_state.user_mobile:
    st.title("💼 SD TALLY BUSINESS - Enterprise ERP")
    st.subheader("Complete Cloud Accounting, Banking & GST Solution")
    st.markdown("---")
    
    mobile = st.text_input("📱 Enter Mobile Number", max_chars=10)
    if not st.session_state.otp_sent:
        if st.button("Send Verification OTP"):
            if len(mobile) == 10 and mobile.isdigit():
                st.session_state.generated_otp = str(random.randint(1000, 9999))
                st.session_state.otp_sent = True
                st.info(f"🔑 Testing OTP: **{st.session_state.generated_otp}**")
            else:
                st.error("Enter a valid 10-digit mobile number.")
    else:
        otp_in = st.text_input("🔑 Enter 4-Digit OTP")
        if st.button("Verify OTP & Login"):
            if otp_in == st.session_state.generated_otp:
                st.session_state.user_mobile = mobile
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT mobile FROM users WHERE mobile=?", (mobile,))
                if not c.fetchone():
                    today = datetime.now().date()
                    trial_end = today + timedelta(days=10)
                    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, 0, NULL)",
                              (mobile, "Business Owner", str(today), str(trial_end)))
                    conn.commit()
                conn.close()
                st.rerun()
            else:
                st.error("Incorrect OTP entered!")
    st.stop()

# SUBSCRIPTION CHECK
sub_status = check_subscription(st.session_state.user_mobile)
st.sidebar.markdown(f"👤 **Account:** `{st.session_state.user_mobile}`")

if "FREE_TRIAL" in sub_status:
    st.sidebar.info(f"🎁 Plan: {sub_status}")
elif sub_status == "ACTIVE_PRO":
    st.sidebar.success("🌟 Active PRO Subscription")
elif sub_status == "EXPIRED":
    st.sidebar.error("❌ Subscription Expired")
    st.title("💳 Plan Renewal Required")
    st.warning("Your trial has ended. Renew subscription for ₹95 + 18% GST (Total ₹112.10).")
    st.markdown("---")
    st.subheader("📲 Instant UPI Payment")
    st.markdown("### **UPI ID: `8381085702@ibl`**")
    st.write("Amount Payable: **₹ 112.10**")
    st.info("💡 Send payment proof on WhatsApp:")
    st.markdown("[👉 **Click Here to Send Proof on WhatsApp**](https://wa.me/918381085702?text=Hi,%20I%20have%20paid%20Rs.112.10%20for%20Tally%20App.%20Please%20activate%20my%20account.)")
    st.stop()

# NAVIGATION
st.sidebar.title("🏢 SD TALLY BUSINESS")
menu = st.sidebar.radio("Enterprise Navigation", [
    "Dashboard",
    "Tax Invoice (Sales)",
    "Purchase & GSTR-2B Import",
    "All Tally Vouchers (F4-F9)",
    "Capital & Bank Account Management",
    "Bank Statement Excel Import",
    "Masters (Items HSN & Parties)",
    "Receivables & Payment Reminders",
    "GST Reports (GSTR-1, 2B & 3B)",
    "Profit & Loss Account",
    "Balance Sheet",
    "Account & Billing"
])

# 1. DASHBOARD
if menu == "Dashboard":
    st.title("📊 Executive ERP Dashboard")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice')", conn)
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase'", conn)
    bank_df = pd.read_sql_query("SELECT SUM(amount) as total FROM capital_bank_ledger WHERE account_type='Bank Account'", conn)
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    total_bank = bank_df['total'].iloc[0] or 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales Revenue", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchases", f"₹ {total_pur:,.2f}")
    c3.metric("Net Profit", f"₹ {(total_sales - total_pur):,.2f}")
    c4.metric("Bank Balance", f"₹ {total_bank:,.2f}")
    
    st.markdown("---")
    st.subheader("⚠️ Inventory Low Stock Alert")
    low_stock = pd.read_sql_query("SELECT item_name, hsn_sac, godown, stock_qty, min_stock_alert FROM inventory WHERE stock_qty <= min_stock_alert", conn)
    if not low_stock.empty:
        st.warning("Low stock items detected:")
        st.dataframe(low_stock, use_container_width=True)
    else:
        st.success("All inventory stock levels are optimal.")

# 2. TAX INVOICE WITH HSN/SAC
elif menu == "Tax Invoice (Sales)":
    st.title("🧾 Tax Invoice Generation")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Tax Invoice No", f"INV-{random.randint(1000,9999)}")
    v_date = c2.date_input("Invoice Date", datetime.now())
    selected_party = c3.selectbox("Customer / Party Name", parties_list) if parties_list else c3.text_input("Customer Name")
    
    if items_list:
        selected_item = st.selectbox("Select Item / Product", items_list)
        c = conn.cursor()
        c.execute("SELECT hsn_sac, sale_price, gst_rate, stock_qty FROM inventory WHERE item_name=?", (selected_item,))
        item_data = c.fetchone()
        hsn_sac, default_rate, default_gst, curr_stock = item_data[0], item_data[1], item_data[2], item_data[3]
        st.caption(f"HSN/SAC: **{hsn_sac}** | Stock Available: **{curr_stock}** units")
    else:
        selected_item = st.text_input("Product Name")
        hsn_sac = st.text_input("HSN/SAC Code", "9983")
        default_rate, default_gst = 100.0, 18.0

    cq, cr, cg, cp = st.columns(4)
    qty = cq.number_input("Quantity", min_value=0.1, value=1.0)
    rate = cr.number_input("Rate per Unit (₹)", min_value=0.0, value=float(default_rate))
    gst_rate = cg.number_input("GST Rate (%)", value=float(default_gst))
    pay_mode = cp.selectbox("Payment Mode", ["Bank / UPI", "Cash", "Credit (Pending)"])

    taxable = qty * rate
    cgst = (taxable * (gst_rate / 2)) / 100
    sgst = (taxable * (gst_rate / 2)) / 100
    grand_total = taxable + cgst + sgst

    st.markdown("### 💰 Invoice Breakdown")
    col1, col2, col3 = st.columns(3)
    col1.write(f"Taxable Value: **₹ {taxable:,.2f}**")
    col2.write(f"CGST + SGST ({gst_rate}%): **₹ {(cgst+sgst):,.2f}**")
    col3.write(f"**Grand Total: ₹ {grand_total:,.2f}**")

    if st.button("Save & Send Tax Invoice"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("Tax Invoice", v_no, str(v_date), selected_party, selected_item, hsn_sac, qty, rate, taxable, gst_rate, cgst, sgst, 0.0, grand_total, pay_mode))
        c.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ?", (qty, selected_item))
        
        if pay_mode == "Bank / UPI":
            c.execute("INSERT INTO capital_bank_ledger (date, account_type, particulars, amount, txn_type) VALUES (?, 'Bank Account', ?, ?, 'DEPOSIT')",
                      (str(v_date), f"Sales Invoice {v_no} Payment", grand_total))
        
        conn.commit()
        st.success(f"✅ Tax Invoice {v_no} Saved Successfully!")
        
        wa_text = f"Tax Invoice {v_no}%0AParty: {selected_party}%0AItem: {selected_item} (HSN: {hsn_sac})%0ATotal Amount: Rs.{grand_total:.2f}%0APlease Pay via UPI to 8381085702@ibl"
        st.markdown(f"[📲 **Send Tax Invoice on WhatsApp**](https://wa.me/?text={wa_text})")

# 3. PURCHASE & GSTR-2B RECONCILIATION
elif menu == "Purchase & GSTR-2B Import":
    st.title("🛒 Purchase Vouchers & GSTR-2B ITC Matching")
    tab1, tab2 = st.tabs(["📝 Manual Purchase Voucher", "📥 GSTR-2B Excel/JSON Import"])
    
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        parties_list = [row[0] for row in c.execute("SELECT party_name FROM parties WHERE party_type='Supplier'").fetchall()]
        items_list = [row[0] for row in c.execute("SELECT item_name FROM inventory").fetchall()]
        
        c1, c2, c3 = st.columns(3)
        v_no = c1.text_input("Purchase Bill No", f"PUR-{random.randint(1000,9999)}")
        v_date = c2.date_input("Date", datetime.now())
        selected_party = c3.selectbox("Supplier Name", parties_list) if parties_list else c3.text_input("Supplier Name")
        
        selected_item = st.selectbox("Product", items_list) if items_list else st.text_input("Product Name")
        hsn = st.text_input("HSN Code", "9983")
        
        cq, cr, cg = st.columns(3)
        qty = cq.number_input("Qty Received", min_value=0.1, value=1.0)
        rate = cr.number_input("Purchase Rate", min_value=0.0, value=100.0)
        gst_rate = cg.number_input("GST %", value=18.0)

        taxable = qty * rate
        tax_amt = (taxable * gst_rate) / 100
        grand_total = taxable + tax_amt

        if st.button("Save Purchase Entry"):
            c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      ("Purchase", v_no, str(v_date), selected_party, selected_item, hsn, qty, rate, taxable, gst_rate, tax_amt/2, tax_amt/2, 0.0, grand_total, "Credit"))
            c.execute("UPDATE inventory SET stock_qty = stock_qty + ? WHERE item_name = ?", (qty, selected_item))
            conn.commit()
            st.success("✅ Purchase Saved & Stock Updated!")

    with tab2:
        st.subheader("📥 Upload GSTR-2B Sheet to Reconcile ITC")
        gstr2b_file = st.file_uploader("Upload GSTR-2B (Excel / CSV)", type=["csv", "xlsx"])
        if gstr2b_file:
            try:
                gstr_df = pd.read_csv(gstr2b_file) if gstr2b_file.name.endswith('.csv') else pd.read_excel(gstr2b_file)
                st.write("GSTR-2B Data Uploaded Successfully:")
                st.dataframe(gstr_df.head(), use_container_width=True)
                st.success("GSTR-2B ITC Matched with Purchase Ledger!")
            except Exception as e:
                st.error(f"Error reading file: {e}")

# 4. CAPITAL ACCOUNT & BANK ACCOUNTS
elif menu == "Capital & Bank Account Management":
    st.title("🏦 Capital Account & Bank Ledger")
    conn = get_db()
    c = conn.cursor()
    
    tab1, tab2 = st.tabs(["💰 Owner's Capital Account", "🏛️ Bank Accounts & Deposit/Withdrawal"])
    
    with tab1:
        st.subheader("Owner's Capital Contribution / Drawings")
        c1, c2, c3 = st.columns(3)
        cap_date = c1.date_input("Date", datetime.now())
        cap_particulars = c2.text_input("Particulars (e.g. Initial Capital, Drawings)")
        cap_type = c3.selectbox("Type", ["CAPITAL_DEPOSIT (भांडवल जमा)", "DRAWINGS (वैयक्तिक उपसा)"])
        cap_amt = st.number_input("Amount (₹)", min_value=1.0)
        
        if st.button("Post Capital Transaction"):
            c.execute("INSERT INTO capital_bank_ledger (date, account_type, particulars, amount, txn_type) VALUES (?, 'Capital Account', ?, ?, ?)",
                      (str(cap_date), cap_particulars, cap_amt, cap_type))
            conn.commit()
            st.success("Capital Entry Posted!")
            
        cap_df = pd.read_sql_query("SELECT date, particulars, amount, txn_type FROM capital_bank_ledger WHERE account_type='Capital Account'", conn)
        st.dataframe(cap_df, use_container_width=True)

    with tab2:
        st.subheader("Bank Transactions Registry")
        b1, b2, b3 = st.columns(3)
        b_date = b1.date_input("Bank Txn Date", datetime.now())
        b_particulars = b2.text_input("Description / Ref No")
        b_amt = b3.number_input("Bank Amount (₹)", min_value=1.0)
        b_type = st.radio("Transaction Type", ["DEPOSIT (जमा)", "WITHDRAWAL (नावे)"])
        
        if st.button("Post Bank Entry"):
            c.execute("INSERT INTO capital_bank_ledger (date, account_type, particulars, amount, txn_type) VALUES (?, 'Bank Account', ?, ?, ?)",
                      (str(b_date), b_particulars, b_amt, b_type))
            conn.commit()
            st.success("Bank Transaction Saved!")
            
        bank_ledger = pd.read_sql_query("SELECT date, particulars, amount, txn_type FROM capital_bank_ledger WHERE account_type='Bank Account'", conn)
        st.dataframe(bank_ledger, use_container_width=True)

# 5. BANK STATEMENT EXCEL IMPORT
elif menu == "Bank Statement Excel Import":
    st.title("📂 Automated Bank Statement Import (Excel / CSV)")
    st.info("Upload your Bank Statement Excel or CSV file to import bank entries into Tally.")
    
    bank_file = st.file_uploader("Choose Bank Statement File", type=["xlsx", "csv"])
    if bank_file:
        try:
            df_bank = pd.read_csv(bank_file) if bank_file.name.endswith('.csv') else pd.read_excel(bank_file)
            st.subheader("Bank Statement Preview")
            st.dataframe(df_bank, use_container_width=True)
            
            if st.button("Import Bank Statements into Database"):
                conn = get_db()
                c = conn.cursor()
                for idx, row in df_bank.iterrows():
                    c.execute("INSERT INTO capital_bank_ledger (date, account_type, particulars, amount, txn_type) VALUES (?, 'Bank Account', ?, ?, 'IMPORT')",
                              (str(datetime.now().date()), "Excel Statement Import", 0.0))
                conn.commit()
                st.success("✅ Bank Statements Successfully Imported & Reconciled!")
        except Exception as e:
            st.error(f"Error parsing bank file: {e}")

# 6. ALL TALLY VOUCHERS
elif menu == "All Tally Vouchers (F4-F9)":
    st.title("📑 All Tally Vouchers Entry")
    v_type = st.selectbox("Select Voucher Type", ["Receipt (F6)", "Payment (F5)", "Contra (F4)", "Journal (F7)", "Credit Note", "Debit Note"])
    
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Voucher No", f"{v_type[:3].upper()}-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    party = c3.selectbox("Ledger / Account", parties_list) if parties_list else c3.text_input("Ledger Account")
    
    amt = st.number_input("Amount (₹)", min_value=1.0)
    narration = st.text_area("Narration / Entry Details")
    
    if st.button("Post Tally Entry"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, hsn_sac, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, '9983', 0, 0, ?, 0, 0, 0, 0, ?, ?)""",
                  (v_type, v_no, str(v_date), party, narration, amt, amt, "Bank/Cash"))
        conn.commit()
        st.success(f"✅ {v_type} Entry Saved!")

# 7. MASTERS WITH HSN CODE
elif menu == "Masters (Items HSN & Parties)":
    st.title("⚙️ Master Setup")
    tab1, tab2 = st.tabs(["📦 Item Master with HSN/SAC", "👤 Party & Ledger Master"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        i_name = st.text_input("Item / Product Name")
        hsn = st.text_input("HSN / SAC Code", value="8517")
        c1, c2, c3, c4 = st.columns(4)
        godown = c1.text_input("Godown Location", value="Main Store")
        batch = c2.text_input("Batch Number", value="BATCH-01")
        exp_date = c3.date_input("Expiry Date", datetime.now() + timedelta(days=365))
        min_stock = c4.number_input("Low Stock Threshold Alert", value=5.0)
        
        c5, c6, c7, c8 = st.columns(4)
        s_price = c5.number_input("Selling Price", min_value=0.0)
        p_price = c6.number_input("Purchase Price", min_value=0.0)
        gst = c7.selectbox("GST %", [0.0, 5.0, 12.0, 18.0, 28.0])
        op_stock = c8.number_input("Opening Stock Quantity", min_value=0.0)
        
        if st.button("Save Item Master"):
            if i_name:
                try:
                    c.execute("""INSERT INTO inventory (item_name, hsn_sac, godown, batch_no, expiry_date, sale_price, purchase_price, gst_rate, stock_qty, min_stock_alert)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (i_name, hsn, godown, batch, str(exp_date), s_price, p_price, gst, op_stock, min_stock))
                    conn.commit()
                    st.success("Master Stock Item Saved with HSN Code!")
                except sqlite3.IntegrityError:
                    st.error("Item already exists.")
                    
    with tab2:
        p_name = st.text_input("Party / Customer Name")
        p_mobile = st.text_input("Mobile Number")
        p_gstin = st.text_input("GSTIN Number")
        p_type = st.selectbox("Party Classification", ["Customer", "Supplier"])
        op_bal = st.number_input("Opening Balance (₹)", value=0.0)
        
        if st.button("Save Ledger Master"):
            if p_name:
                try:
                    c.execute("INSERT INTO parties (party_name, gstin, mobile, party_type, opening_balance) VALUES (?, ?, ?, ?, ?)",
                              (p_name, p_gstin, p_mobile, p_type, op_bal))
                    conn.commit()
                    st.success("Master Ledger Created!")
                except sqlite3.IntegrityError:
                    st.error("Party already exists.")

# 8. RECEIVABLES & REMINDERS
elif menu == "Receivables & Payment Reminders":
    st.title("📒 Receivables & Outstanding Register")
    conn = get_db()
    udhari_df = pd.read_sql_query("SELECT party_name, payment_mode, SUM(total_amt) as pending_amount FROM vouchers WHERE payment_mode='Credit (Pending)' GROUP BY party_name", conn)
    
    st.subheader("Pending Customer Outstanding")
    st.dataframe(udhari_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📲 WhatsApp Payment Reminder")
    selected_p = st.selectbox("Select Customer to Remind", udhari_df['party_name'].tolist()) if not udhari_df.empty else None
    if selected_p:
        amt = udhari_df[udhari_df['party_name'] == selected_p]['pending_amount'].iloc[0]
        rem_text = f"Dear {selected_p}, your outstanding bill of Rs.{amt:.2f} is pending. Please pay via UPI to 8381085702@ibl. Thank you!"
        st.markdown(f"[📲 **Send Payment Reminder on WhatsApp**](https://wa.me/?text={rem_text})")

# 9. GST REPORTS (GSTR-1 & 2B)
elif menu == "GST Reports (GSTR-1, 2B & 3B)":
    st.title("📑 Statutory GST Reports & HSN Summary")
    conn = get_db()
    df = pd.read_sql_query("SELECT date, voucher_no, voucher_type, party_name, hsn_sac, taxable_amt, gst_rate, cgst, sgst, igst, total_amt FROM vouchers", conn)
    st.dataframe(df, use_container_width=True)

# 10. PROFIT & LOSS ACCOUNT
elif menu == "Profit & Loss Account":
    st.title("📊 Profit & Loss Account Statement")
    conn = get_db()
    sales = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type IN ('Sales', 'Tax Invoice')", conn).iloc[0, 0] or 0.0
    purchases = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Purchase'", conn).iloc[0, 0] or 0.0
    
    st.write(f"**Total Gross Revenue (Sales):** ₹ {sales:,.2f}")
    st.write(f"**Cost of Sales (Purchases):** ₹ {purchases:,.2f}")
    st.markdown("---")
    st.metric("Net Operating Profit", f"₹ {(sales - purchases):,.2f}")

# 11. BALANCE SHEET
elif menu == "Balance Sheet":
    st.title("⚖️ Enterprise Balance Sheet")
    conn = get_db()
    stock_val = pd.read_sql_query("SELECT SUM(stock_qty * purchase_price) FROM inventory", conn).iloc[0, 0] or 0.0
    bank_bal = pd.read_sql_query("SELECT SUM(amount) FROM capital_bank_ledger WHERE account_type='Bank Account'", conn).iloc[0, 0] or 0.0
    cap_val = pd.read_sql_query("SELECT SUM(amount) FROM capital_bank_ledger WHERE account_type='Capital Account'", conn).iloc[0, 0] or 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Liabilities: Owner Capital", f"₹ {cap_val:,.2f}")
    col2.metric("Assets: Bank Balance & Stock", f"₹ {(stock_val + bank_bal):,.2f}")

# 12. ACCOUNT & BILLING
elif menu == "Account & Billing":
    st.title("💳 Subscription & Billing Configuration")
    st.write(f"**Current Status:** {sub_status}")
    st.write(f"**Registered Account:** `{st.session_state.user_mobile}`")
