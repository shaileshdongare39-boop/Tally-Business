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
st.set_page_config(page_title="Tally & Vyapar Ultimate Business Suite", layout="wide", page_icon="📊")

# Database Initialization
DB_FILE = "tally_vyapar_master.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    mobile TEXT PRIMARY KEY,
                    name TEXT,
                    reg_date TEXT,
                    trial_end_date TEXT,
                    is_paid INTEGER DEFAULT 0,
                    paid_till TEXT
                )''')
    # Inventory Table (With Tally Batch/Expiry + Vyapar Low Stock)
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT UNIQUE,
                    godown TEXT,
                    batch_no TEXT,
                    expiry_date TEXT,
                    sale_price REAL,
                    purchase_price REAL,
                    gst_rate REAL,
                    stock_qty REAL,
                    min_stock_alert REAL DEFAULT 5
                )''')
    # Parties Table (Customers & Suppliers)
    c.execute('''CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT UNIQUE,
                    gstin TEXT,
                    mobile TEXT,
                    party_type TEXT,
                    opening_balance REAL DEFAULT 0
                )''')
    # All Vouchers Table (Tally + Vyapar)
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
                    igst REAL,
                    total_amt REAL,
                    payment_mode TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Multi-language Support
I18N = {
    "English": {
        "title": "Tally & Vyapar Ultimate Business Suite",
        "nav": ["Dashboard", "Sales Invoice (Vyapar Quick)", "Purchase Invoice", "All Vouchers (Tally F4-F9)", "Masters (Items & Parties)", "Udhari / Receivables Register", "GST Reports (GSTR-1/3B)", "Profit & Loss", "Balance Sheet", "Subscription & Billing"],
        "sales": "Sales Invoice", "purchase": "Purchase Invoice", "party": "Party / Customer Name", "item": "Item / Product",
        "qty": "Quantity", "rate": "Rate", "save": "Save & Print Invoice"
    },
    "मराठी": {
        "title": "टॅली व व्यापार अल्टीमेट बिझनेस सूट",
        "nav": ["डॅशबोर्ड (Dashboard)", "विक्री बिल (Vyapar Quick)", "खरेदी बिल (Purchase)", "सर्व व्हॉउचर्स (Tally F4-F9)", "मास्टर्स (Items & Parties)", "उधारी / बाकी रजिस्टर", "GST रिपोर्ट्स (GSTR-1/3B)", "नफा आणि तोटा (P&L)", "ताळेबंद (Balance Sheet)", "वर्गणी आणि बिलिंग"],
        "sales": "नवीन विक्री बिल", "purchase": "नवीन खरेदी बिल", "party": "ग्राहकाचे/पार्टीचे नाव", "item": "वस्तू/माल (Item)",
        "qty": "नग/प्रमाण (Qty)", "rate": "दर (Rate)", "save": "बिल सेव्ह करा"
    }
}

lang = st.sidebar.selectbox("🌐 Choose Language / भाषा निवडा", ["मराठी", "English"])
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
    st.title("🔐 Login / Register (Tally & Vyapar Cloud)")
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
                              (mobile, "Business Owner", str(today), str(trial_end)))
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
    st.warning("तुमचा १० दिवसांचा मोफत वापर संपला आहे. पुढे वापरण्यासाठी ₹95 + 18% GST (Total ₹112.10) भरून ॲप सुरू करा.")
    
    st.markdown("---")
    st.subheader("📲 Scan / Pay via Any UPI App (PhonePe / GPay / Paytm)")
    st.markdown("### **UPI ID: `8381085702@ibl`**")
    st.write("एकूण रक्कम: **₹ 112.10**")
    
    st.info("💡 पेमेंट केल्यावर पेमेंटचा स्क्रीनशॉट आणि तुमचा रजिस्टर मोबाईल नंबर खालील बटणावर क्लिक करून WhatsApp वर पाठवा:")
    st.markdown("[👉 **इथे क्लिक करून WhatsApp वर स्क्रीनशॉट पाठवा**](https://wa.me/918381085702?text=Hi,%20I%20have%20paid%20Rs.112.10%20for%20Tally%20App.%20Please%20activate%20my%20account.)")
    st.stop()

# NAVIGATION
st.sidebar.title("📊 Menu Navigation")
menu = st.sidebar.radio("Go To:", t["nav"])

# 1. DASHBOARD
if menu == t["nav"][0]:
    st.title("📊 Business Performance Dashboard")
    conn = get_db()
    sales_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type IN ('Sales', 'Sales Invoice')", conn)
    pur_df = pd.read_sql_query("SELECT SUM(total_amt) as total FROM vouchers WHERE voucher_type='Purchase'", conn)
    
    total_sales = sales_df['total'].iloc[0] or 0.0
    total_pur = pur_df['total'].iloc[0] or 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales (एकूण विक्री)", f"₹ {total_sales:,.2f}")
    c2.metric("Total Purchases (एकूण खरेदी)", f"₹ {total_pur:,.2f}")
    c3.metric("Net Profit (निव्वळ नफा)", f"₹ {(total_sales - total_pur):,.2f}")
    
    # Low Stock Warning (Vyapar Feature)
    st.markdown("---")
    st.subheader("⚠️ Low Stock Alert (कमी साठा सूचना)")
    low_stock = pd.read_sql_query("SELECT item_name, stock_qty, min_stock_alert FROM inventory WHERE stock_qty <= min_stock_alert", conn)
    if not low_stock.empty:
        st.warning("खालील वस्तूंचा साठा संपत आला आहे:")
        st.dataframe(low_stock, use_container_width=True)
    else:
        st.success("सर्व वस्तूंचा साठा मुबलक आहे.")

# 2. QUICK SALES INVOICE (Vyapar + Tally)
elif menu == t["nav"][1]:
    st.title("🧾 Quick Sales Invoice (व्यापार बिलिंग)")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Invoice No", f"INV-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    selected_party = c3.selectbox(t["party"], parties_list) if parties_list else c3.text_input(t["party"])
    
    if items_list:
        selected_item = st.selectbox(t["item"], items_list)
        c = conn.cursor()
        c.execute("SELECT sale_price, gst_rate, stock_qty FROM inventory WHERE item_name=?", (selected_item,))
        item_data = c.fetchone()
        default_rate, default_gst, curr_stock = item_data[0], item_data[1], item_data[2]
        st.caption(f"Current Available Stock: **{curr_stock}** units")
    else:
        selected_item = st.text_input(t["item"])
        default_rate, default_gst = 100.0, 18.0

    cq, cr, cg, cp = st.columns(4)
    qty = cq.number_input(t["qty"], min_value=0.1, value=1.0)
    rate = cr.number_input(t["rate"], min_value=0.0, value=float(default_rate))
    gst_rate = cg.number_input("GST Rate (%)", value=float(default_gst))
    pay_mode = cp.selectbox("Payment Mode", ["Cash", "UPI (PhonePe/GPay)", "Credit (उधारी)"])

    taxable = qty * rate
    cgst = (taxable * (gst_rate / 2)) / 100
    sgst = (taxable * (gst_rate / 2)) / 100
    grand_total = taxable + cgst + sgst

    st.markdown("### 💰 Grand Total")
    st.subheader(f"Total Bill Amount: ₹ {grand_total:,.2f}")

    if st.button(t["save"]):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("Sales Invoice", v_no, str(v_date), selected_party, selected_item, qty, rate, taxable, gst_rate, cgst, sgst, 0.0, grand_total, pay_mode))
        c.execute("UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ?", (qty, selected_item))
        conn.commit()
        st.success(f"✅ Sales Invoice {v_no} Created!")
        
        # WhatsApp Share Link (Vyapar Feature)
        wa_text = f"Hello {selected_party}, your bill {v_no} of Rs.{grand_total:.2f} is generated. Thank you!"
        st.markdown(f"[📲 **Send Invoice via WhatsApp**](https://wa.me/?text={wa_text})")

# 3. PURCHASE INVOICE
elif menu == t["nav"][2]:
    st.title("🛒 Purchase Voucher Entry")
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties WHERE party_type='Supplier'").fetchall()]
    items_list = [row[0] for row in conn.execute("SELECT item_name FROM inventory").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Purchase No", f"PUR-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    selected_party = c3.selectbox("Supplier Name", parties_list) if parties_list else c3.text_input("Supplier Name")
    
    selected_item = st.selectbox("Item Name", items_list) if items_list else st.text_input("Item Name")
    cq, cr, cg = st.columns(3)
    qty = cq.number_input("Qty Received", min_value=0.1, value=1.0)
    rate = cr.number_input("Purchase Rate", min_value=0.0, value=100.0)
    gst_rate = cg.number_input("GST %", value=18.0)

    taxable = qty * rate
    total_tax = (taxable * gst_rate) / 100
    grand_total = taxable + total_tax

    if st.button("Save Purchase Voucher"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  ("Purchase", v_no, str(v_date), selected_party, selected_item, qty, rate, taxable, gst_rate, total_tax/2, total_tax/2, 0.0, grand_total, "Credit"))
        c.execute("UPDATE inventory SET stock_qty = stock_qty + ? WHERE item_name = ?", (qty, selected_item))
        conn.commit()
        st.success("✅ Purchase Saved & Stock Updated!")

# 4. ALL TALLY VOUCHERS (Receipt, Payment, Contra, Journal, Notes)
elif menu == t["nav"][3]:
    st.title("📑 All Tally Vouchers (Receipt / Payment / Contra / Journal)")
    v_type = st.selectbox("Select Tally Voucher Type", ["Receipt (F6)", "Payment (F5)", "Contra (F4)", "Journal (F7)", "Credit Note", "Debit Note"])
    
    conn = get_db()
    parties_list = [row[0] for row in conn.execute("SELECT party_name FROM parties").fetchall()]
    
    c1, c2, c3 = st.columns(3)
    v_no = c1.text_input("Voucher Number", f"{v_type[:3].upper()}-{random.randint(1000,9999)}")
    v_date = c2.date_input("Date", datetime.now())
    party = c3.selectbox("Party Name", parties_list) if parties_list else c3.text_input("Party Name")
    
    amt = st.number_input("Amount (₹)", min_value=1.0)
    narration = st.text_area("Narration / Description")
    
    if st.button("Save Voucher Entry"):
        c = conn.cursor()
        c.execute("""INSERT INTO vouchers (voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amt, gst_rate, cgst, sgst, igst, total_amt, payment_mode)
                     VALUES (?, ?, ?, ?, ?, 0, 0, ?, 0, 0, 0, 0, ?, ?)""",
                  (v_type, v_no, str(v_date), party, narration, amt, amt, "Bank/Cash"))
        conn.commit()
        st.success(f"✅ {v_type} Voucher Saved Successfully!")

# 5. MASTERS (Items with Batch/Godown & Parties)
elif menu == t["nav"][4]:
    st.title("⚙️ Masters Creation")
    tab1, tab2 = st.tabs(["📦 Item & Stock Master (Tally+Vyapar)", "👤 Party Master (Customer/Supplier)"])
    conn = get_db()
    c = conn.cursor()
    
    with tab1:
        i_name = st.text_input("Item Name")
        c1, c2, c3, c4 = st.columns(4)
        godown = c1.text_input("Godown / Location", value="Main Store")
        batch = c2.text_input("Batch No", value="BATCH-01")
        exp_date = c3.date_input("Expiry Date", datetime.now() + timedelta(days=365))
        min_stock = c4.number_input("Low Stock Alert Qty", value=5.0)
        
        c5, c6, c7, c8 = st.columns(4)
        s_price = c5.number_input("Selling Price", min_value=0.0)
        p_price = c6.number_input("Purchase Price", min_value=0.0)
        gst = c7.selectbox("GST Rate %", [0.0, 5.0, 12.0, 18.0, 28.0])
        op_stock = c8.number_input("Opening Stock", min_value=0.0)
        
        if st.button("Save Master Item"):
            if i_name:
                try:
                    c.execute("""INSERT INTO inventory (item_name, godown, batch_no, expiry_date, sale_price, purchase_price, gst_rate, stock_qty, min_stock_alert)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (i_name, godown, batch, str(exp_date), s_price, p_price, gst, op_stock, min_stock))
                    conn.commit()
                    st.success("Item Saved with Godown & Batch Details!")
                except sqlite3.IntegrityError:
                    st.error("Item already exists.")
                    
    with tab2:
        p_name = st.text_input("Party Name")
        p_mobile = st.text_input("Mobile Number")
        p_gstin = st.text_input("GSTIN Number (Optional)")
        p_type = st.selectbox("Party Type", ["Customer", "Supplier"])
        op_bal = st.number_input("Opening Balance (₹)", value=0.0)
        
        if st.button("Save Party Master"):
            if p_name:
                try:
                    c.execute("INSERT INTO parties (party_name, gstin, mobile, party_type, opening_balance) VALUES (?, ?, ?, ?, ?)",
                              (p_name, p_gstin, p_mobile, p_type, op_bal))
                    conn.commit()
                    st.success("Party Saved!")
                except sqlite3.IntegrityError:
                    st.error("Party already exists.")

# 6. UDHARI / RECEIVABLES REGISTER (Vyapar Feature)
elif menu == t["nav"][5]:
    st.title("📒 Udhari / Receivables & Payables Register")
    conn = get_db()
    udhari_df = pd.read_sql_query("SELECT party_name, payment_mode, SUM(total_amt) as pending_amount FROM vouchers WHERE payment_mode='Credit (उधारी)' GROUP BY party_name", conn)
    
    st.subheader(" ग्राहकनिहाय बाकी रक्कम (Pending Udhari)")
    st.dataframe(udhari_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📲 Send Payment Reminder via WhatsApp")
    selected_p = st.selectbox("Select Customer to Send Reminder", udhari_df['party_name'].tolist()) if not udhari_df.empty else None
    if selected_p:
        amt = udhari_df[udhari_df['party_name'] == selected_p]['pending_amount'].iloc[0]
        rem_text = f"Dear {selected_p}, your payment of Rs.{amt:.2f} is pending. Please pay via UPI to 8381085702@ibl. Thank you!"
        st.markdown(f"[📲 **WhatsApp Reminder पाठवा**](https://wa.me/?text={rem_text})")

# 7. GST REPORTS (GSTR-1 & GSTR-3B)
elif menu == t["nav"][6]:
    st.title("📑 GST Reports (GSTR-1 & GSTR-3B Summary)")
    conn = get_db()
    df = pd.read_sql_query("SELECT date, voucher_no, voucher_type, party_name, taxable_amt, gst_rate, cgst, sgst, igst, total_amt FROM vouchers", conn)
    st.dataframe(df, use_container_width=True)

# 8. PROFIT & LOSS ACCOUNT
elif menu == t["nav"][7]:
    st.title("📊 Profit & Loss Account (नफा-तोटा पत्रक)")
    conn = get_db()
    sales = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type IN ('Sales', 'Sales Invoice')", conn).iloc[0, 0] or 0.0
    purchases = pd.read_sql_query("SELECT SUM(taxable_amt) FROM vouchers WHERE voucher_type='Purchase'", conn).iloc[0, 0] or 0.0
    
    st.write(f"**Total Revenue / Sales:** ₹ {sales:,.2f}")
    st.write(f"**Total Cost / Purchases:** ₹ {purchases:,.2f}")
    st.markdown("---")
    st.metric("Net Profit / Gross Margin", f"₹ {(sales - purchases):,.2f}")

# 9. BALANCE SHEET
elif menu == t["nav"][8]:
    st.title("⚖️ Balance Sheet (ताळेबंद)")
    conn = get_db()
    stock_val = pd.read_sql_query("SELECT SUM(stock_qty * purchase_price) FROM inventory", conn).iloc[0, 0] or 0.0
    cash_bank = pd.read_sql_query("SELECT SUM(total_amt) FROM vouchers WHERE payment_mode IN ('Cash', 'Bank/Cash', 'UPI (PhonePe/GPay)')", conn).iloc[0, 0] or 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Assets: Closing Stock Value", f"₹ {stock_val:,.2f}")
    col2.metric("Assets: Cash & Bank Balance", f"₹ {cash_bank:,.2f}")

# 10. SUBSCRIPTION & BILLING
elif menu == t["nav"][9]:
    st.title("💳 Subscription & Account Status")
    st.write(f"**Current Status:** {sub_status}")
    st.write(f"**Registered Mobile:** `{st.session_state.user_mobile}`")
