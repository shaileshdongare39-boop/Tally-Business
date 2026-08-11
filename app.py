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
st.set_page_config(page_title="Tally Prime Web Edition", layout="wide", page_icon="📊")

# Database Initialization
DB_FILE = "tally_business.db"

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
                    sale_price REAL,
                    purchase_price REAL,
                    gst_rate REAL,
                    stock_qty REAL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT UNIQUE,
                    gstin TEXT,
                    party_type TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voucher_type TEXT,
                    voucher_no TEXT,
                    date TEXT,
                    party_name TEXT,
                    item_name TEXT,
                    qty REAL,
                    rate REAL,
                    taxable_amt REAL,
                    gst_rate REAL,
                    cgst REAL,
                    sgst REAL,
                    total_amt REAL
                )''')
    conn.commit()
    conn.close()

init_db()

# Translations
I18N = {
    "English": {
        "title": "Tally Prime Web Suite",
        "nav": ["Dashboard", "Sales Voucher", "Purchase Voucher", "Masters", "GSTR-1 & Reports", "Profit & Loss", "Balance Sheet", "Subscription & Billing"],
        "sales": "Sales Invoice", "purchase": "Purchase Invoice", "party": "Party Name", "item": "Item / Product",
        "qty": "Quantity", "rate": "Rate", "save": "Save Voucher"
    },
    "मराठी": {
        "title": "टॅली प्राईम वेब सूट",
        "nav": ["डॅशबोर्ड (Dashboard)", "विक्री पावती (Sales)", "खरेदी पावती (Purchase)", "मास्टर्स (Masters)", "GST रिपोर्ट्स", "नफा आणि तोटा (P&L)", "ताळेबंद (Balance Sheet)", "वर्गणी आणि बिलिंग"],
        "sales": "नवीन विक्री बिल", "purchase": "नवीन खरेदी बिल", "party": "ग्राहकाचे/पार्टीचे नाव", "item": "वस्तू/माल (Item)",
        "qty": "नग/प्रमाण (Qty)", "rate": "दर (Rate)", "save": "पावती सेव्ह करा"
    },
    "हिंदी": {
        "title": "टैली प्राइम वेब सूट",
        "nav": ["डैशबोर्ड", "बिक्री वाउचर", "खरीद वाउचर", "मास्टर्स", "जीएसटी रिपोर्ट", "लाभ और हानि", "बैलेंस शीट", "सदस्यता और बिलिंग"],
        "sales": "बिक्री इनवॉइस", "purchase": "खरीद इनवॉइस", "party": "पार्टी का नाम", "item": "सामान/सामग्री",
        "qty": "मात्रा (Qty)", "rate": "दर (Rate)", "save": "वाउचर सहेजें"
    }
}

lang = st.sidebar.selectbox("🌐 Choose Language / भाषा निवडा", ["English", "मराठी", "हिंदी"])
t = I18N[lang]

# Login & OTP Session
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
    
    if user[2] == 1:
        paid_till = datetime.strptime(user[3], "%Y-%m-%d").date()
        if today <= paid_till:
            return "ACTIVE_PRO"
    
    if today <= trial_end:
        days_left = (trial_end - today).days
        return f"FREE_TRIAL ({days_left} days left)"
    
    return "EXPIRED"

# LOGIN PAGE
if not st.session_state.user_mobile:
    st.title("🔐 Login / Register (Tally Cloud)")
    mobile = st.text_input("📱 Enter Mobile Number", max_chars=10)
    
    if not st.session_state.otp_sent:
        if st.button("Send OTP"):
            if len(mobile) == 10 and mobile.isdigit():
                st.session_state.generated_otp = str(random.randint(1000, 9999))
                st.session_state.otp_sent = True
                st.info(f"🔑 Simulated OTP for testing: **{st.session_state.generated_otp}**")
            else:
                st.error("Invalid mobile number.")
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
                              (mobile, "Business User", str(today), str(trial_end)))
                    conn.commit()
                conn.close()
                st.rerun()
            else:
                st.error("Incorrect OTP!")
    st.stop()

# SUBSCRIPTION CHECK
sub_status = check_subscription(st.session_state.user_mobile)
st.sidebar.markdown(f"**Logged in:** `{st.session_state.user_mobile}`")

if "FREE_TRIAL" in sub_status:
    st.sidebar.info(f"🎁 Trial Active: {sub_status}")
elif sub_status == "ACTIVE_PRO":
    st.sidebar.success("🌟 PRO Account Active")
elif sub_status == "EXPIRED":
    st.sidebar.error("❌ Trial Expired")
    st.title("💳 Renewal Required / प्लॅन संपला आहे")
    st.warning("तुमचा १० दिवसांचा मोफत वापर संपला आहे. आगे वापरण्यासाठी ₹95 + 18% GST (Total ₹112.10) भरून ॲप सुरू करा.")
    
    if st.button("Pay ₹112.10 (Simulate Payment)"):
        conn = get_db()
        c = conn.cursor()
        paid_till = datetime.now().date() + timedelta(days=30)
        c.execute("UPDATE users SET is_paid=1, paid_till=? WHERE mobile=?", (str(paid_till), st.session_state.user_mobile))
        conn.commit()
        conn.close()
        st.success("🎉 Payment Successful!")
        st.rerun()
    st.stop()

# NAVIGATION
st.sidebar.title(t["title"])
menu = st.sidebar.radio("Navigation", t["nav"])

# DASHBOARD
if menu == t["nav"][0]:
    st.title("📊 Business Performance Dashboard")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Sales'", conn)
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase'", conn)
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales (विक्री)", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchases (खरेदी)", f"₹ {total_pur:,.2f}")
    c3.metric("Net Profit", f"₹ {(total_sales - total_pur):,.2f}")

# VOUCHERS (Sales/Purchase)
elif menu in [t["nav"][1], t["nav"][2]]:
    v_type = "Sales" if menu == t["nav"][1] else "Purchase"
    st.title(f"🧾 {v_type} Voucher Entry")
    
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Voucher No", f"{v_type[:3].upper()}-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    selected_party = c3.selectbox(t["party"], parties_list) if parties_list else c3.text_input(t["party"])
    
    if items_list:
        selected_item = st.selectbox(t["item"], items_list)
        c = conn.cursor()
        c.execute("SELECT sale_price, purchase_price, gst_rate FROM inventory WHERE item_name=?", (selected_item,))
        item_data = c.fetchone()
        default_rate = item_data[0] if v_type == "Sales" else item_data[1]
        default_gst = item_data[2]
    else:
        selected_item = st.text_input(t["item"])
        default_rate, default_gst = 100.0, 18.0

    cq, cr, cg = st.columns(3)
    qty = cq.number_input(t["qty"], min_value=0.1, value=1.0)
    rate = cr.number_input(t["rate"], min_value=0.0, value=float(default_rate))
    gst_rate = cg.number_input("GST Rate (%)", value=float(default_gst))

    taxable = qty * rate
    cgst = (taxable * (gst_rate / 2)) / 100
    sgst = (taxable * (gst_rate / 2)) / 100
    grand_total = taxable + cgst + sgst

    st.markdown("### 💰 Bill Total")
    st.subheader(f"Grand Total: ₹ {grand_total:,.2f}")

    if st.button(t["save"]):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, total_amt)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (v_type, v_no, str(v_date), selected_party, selected_item, qty, rate, taxable, gst_rate, cgst, sgst, grand_total))
        stock_change = -qty if v_type == "Sales" else qty
        c.execute("UPDATE inventory SET stock_qty = stock_qty + ? WHERE item_name = ?", (stock_change, selected_item))
        conn.commit()
        st.success(f"✅ {v_type} Saved Successfully!")

# MASTERS
elif menu == t["nav"][3]:
    st.title("⚙️ Masters Creation")
    tab1, tab2 = st.tabs(["📦 Item Master", "👤 Party Master"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        i_name = st.text_input("Item Name")
        c1, c2, c3, c4 = st.columns(4)
        s_price = c1.number_input("Selling Price", min_value=0.0)
        p_price = c2.number_input("Purchase Price", min_value=0.0)
        gst = c3.selectbox("GST Rate %", [0.0, 5.0, 12.0, 18.0, 28.0])
        op_stock = c4.number_input("Opening Stock", min_value=0.0)
        
        if st.button("Save Item"):
            if i_name:
                try:
                    c.execute("INSERT INTO inventory (item_name, sale_price, purchase_price, gst_rate, stock_qty) VALUES (?, ?, ?, ?, ?)",
                              (i_name, s_price, p_price, gst, op_stock))
                    conn.commit()
                    st.success("Item Saved!")
                except sqlite3.IntegrityError:
                    st.error("Item already exists.")
                    
    with tab2:
        p_name = st.text_input("Party Name")
        p_gstin = st.text_input("GSTIN Number")
        p_type = st.selectbox("Type", ["Customer", "Supplier"])
        
        if st.button("Save Party"):
            if p_name:
                try:
                    c.execute("INSERT INTO parties (party_name, gstin, party_type) VALUES (?, ?, ?)", (p_name, p_gstin, p_type))
                    conn.commit()
                    st.success("Party Saved!")
                except sqlite3.IntegrityError:
                    st.error("Party already exists.")

# REPORTS / P&L / BALANCE SHEET
elif menu == t["nav"][4]:
    st.title("📑 GST Reports")
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM vouchers", conn)
    st.dataframe(df, use_container_width=True)

elif menu == t["nav"][5]:
    st.title("📊 Profit & Loss Account")
    conn = get_db()
    sales = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Sales'", conn).iloc[0, 0] or 0.0
    purchases = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Purchase'", conn).iloc[0, 0] or 0.0
    st.metric("Gross Profit", f"₹ {(sales - purchases):,.2f}")

elif menu == t["nav"][6]:
    st.title("⚖️ Balance Sheet")
    conn = get_db()
    stock_val = pd.read_sql_query("SELECT SUM(stock_qty * purchase_price) FROM inventory", conn).iloc[0, 0] or 0.0
    st.metric("Closing Stock Value", f"₹ {stock_val:,.2f}")

elif menu == t["nav"][7]:
    st.title("💳 Subscription Status")
    st.write(f"**Status:** {sub_status}")
