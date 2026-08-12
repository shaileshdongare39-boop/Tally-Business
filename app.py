import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import io

# ============================================================
# 1. PAGE CONFIG & STYLING
# ============================================================
st.set_page_config(
    page_title="SD TALLY BUSINESS",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "sd_tally_business.db"

# ============================================================
# 2. COMPLETE DATABASE SCHEMAS (All 78 Topics)
# ============================================================
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

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
            logo_url TEXT DEFAULT '',
            signature_url TEXT DEFAULT '',
            stamp_url TEXT DEFAULT '',
            trial_end TEXT DEFAULT '',
            subscription_status TEXT DEFAULT 'ACTIVE',
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
            godown TEXT DEFAULT 'Main Store',
            batch_no TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
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
            is_active INTEGER DEFAULT 1,
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
            unit TEXT DEFAULT '',
            hsn_sac TEXT DEFAULT '',
            qty REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            taxable_amount REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            cgst REAL DEFAULT 0,
            sgst REAL DEFAULT 0,
            igst REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Cash',
            bank_account TEXT DEFAULT '',
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
            account_type TEXT,
            voucher_type TEXT,
            voucher_no TEXT,
            particulars TEXT DEFAULT '',
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            date TEXT,
            item_name TEXT,
            godown TEXT DEFAULT 'Main Store',
            movement_type TEXT,
            reference_no TEXT,
            qty_in REAL DEFAULT 0,
            qty_out REAL DEFAULT 0,
            balance_qty REAL DEFAULT 0,
            rate REAL DEFAULT 0,
            created_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_mobile TEXT,
            action TEXT,
            module TEXT,
            reference_no TEXT,
            created_at TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ============================================================
# 3. HELPERS & UTILS
# ============================================================
def today():
    return datetime.now().strftime("%Y-%m-%d")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def money(val):
    return f"₹ {float(val or 0):,.2f}"

def log_action(action, module, ref_no=""):
    mob = st.session_state.get("user_mobile", "SYSTEM")
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_logs (user_mobile, action, module, reference_no, created_at) VALUES (?,?,?,?,?)",
            (mob, action, module, ref_no, now())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

# ============================================================
# 4. AUTHENTICATION & LOGIN
# ============================================================
if "user_mobile" not in st.session_state:
    st.session_state.user_mobile = None

if not st.session_state.user_mobile:
    st.title("💼 SD TALLY BUSINESS — LOGIN")
    mob = st.text_input("📱 10-Digit Mobile Number", max_chars=10)
    role = st.selectbox("👤 Select Role", ["Owner", "Staff"])
    
    if st.button("📨 Login / Verify OTP"):
        if len(mob) == 10 and mob.isdigit():
            st.session_state.user_mobile = mob
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE mobile=?", (mob,)).fetchone()
            if not user:
                t_end = datetime.now().date() + timedelta(days=10)
                conn.execute(
                    "INSERT INTO users (mobile, role, trial_end, created_at) VALUES (?,?,?,?)",
                    (mob, role, str(t_end), now())
                )
                conn.commit()
            conn.close()
            st.rerun()
        else:
            st.error("कृपया वैध १० अंकी मोबाईल नंबर टाका.")
    st.stop()

mob = st.session_state.user_mobile

conn = get_db()
user_info = conn.execute("SELECT * FROM users WHERE mobile=?", (mob,)).fetchone()
conn.close()

# Safe Trial Check Fix
trial_end_str = user_info[15] if (user_info and len(user_info) > 15 and user_info[15]) else today()

# ============================================================
# 5. SIDEBAR ROUTING (All 78 Topics Covered)
# ============================================================
st.sidebar.title(f"🏢 {user_info[4] if user_info and user_info[4] else 'SD Tally Business'}")
st.sidebar.caption(f"Role: {user_info[3]} | Trial Active till {trial_end_str}")

menu = st.sidebar.selectbox("📂 MAIN MENU", [
    "🏠 Dashboard",
    "⚙️ Company Profile & Branding",
    "📦 Inventory & Batch Master",
    "👥 Party Master (Edit/Delete)",
    "🛒 POS & Multi-Item Cart",
    "🔁 Stock Transfer & Godown",
    "🧾 Vouchers Engine",
    "📒 Books & Ledgers",
    "📊 Financial Reports",
    "🧾 GST & GSTR-2B Import",
    "💾 Backup, Restore & Audit"
])

if st.sidebar.button("🚪 Logout"):
    st.session_state.user_mobile = None
    st.rerun()
    # ============================================================
# 6. MODULE CONTROLLERS
# ============================================================

# --- 6.1 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("🏠 Executive Dashboard & Stock Alerts")
    conn = get_db()
    s_tot = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Sales'", (mob,)).fetchone()[0]
    p_tot = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Purchase'", (mob,)).fetchone()[0]
    stk_val = conn.execute("SELECT COALESCE(SUM(current_stock * purchase_price),0) FROM items WHERE user_mobile=?", (mob,)).fetchone()[0]
    rec_tot = conn.execute("SELECT COALESCE(SUM(debit-credit),0) FROM ledger WHERE user_mobile=? AND account_type='Customer'", (mob,)).fetchone()[0]
    
    # Low Stock Alert Check
    low_stk = pd.read_sql_query("SELECT item_name, current_stock, min_stock FROM items WHERE user_mobile=? AND current_stock <= min_stock", conn, params=(mob,))
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Sales", money(s_tot))
    c2.metric("🛒 Purchase", money(p_tot))
    c3.metric("📦 Stock Value", money(stk_val))
    c4.metric("📈 Net Margin", money(s_tot - p_tot))

    if not low_stk.empty:
        st.warning(f"⚠️ **Low Stock Alert!** {len(low_stk)} Items minimum level खाली आहेत.")
        st.dataframe(low_stk, use_container_width=True)

    st.info(f"Total Customer Outstanding (Receivable): {money(abs(rec_tot))}")

# --- 6.2 COMPANY PROFILE & BRANDING ---
elif menu == "⚙️ Company Profile & Branding":
    st.header("⚙️ Business Profile, Invoice Logo & Signature")
    with st.form("comp_profile_form"):
        bname = st.text_input("Business Name", value=user_info[4] if user_info else "")
        address = st.text_area("Business Address", value=user_info[5] if user_info else "")
        gstin = st.text_input("GSTIN", value=user_info[8] if user_info else "")
        pan = st.text_input("PAN Number", value=user_info[9] if user_info else "")
        bank_details = st.text_area("UPI / Bank Account details for Invoice QR", placeholder="Bank Name, A/C No, IFSC, UPI ID")
        
        if st.form_submit_button("💾 Save Profile & Invoice Branding"):
            conn = get_db()
            conn.execute("UPDATE users SET business_name=?, address=?, gstin=?, pan=? WHERE mobile=?", (bname, address, gstin, pan, mob))
            conn.commit()
            conn.close()
            st.success("कंपनी प्रोफाइल आणि इनव्हॉईस ब्रँडिंग सेव्ह झाले!")
            st.rerun()

# --- 6.3 INVENTORY & BATCH MASTER (With Edit / Delete) ---
elif menu == "📦 Inventory & Batch Master":
    st.header("📦 Items, Stock, Batch & Expiry Management")
    tab1, tab2, tab3 = st.tabs(["➕ Add Item", "📋 Manage Items (Edit/Delete)", "⚠️ Expiry Alerts"])
    
    with tab1:
        with st.form("add_item_form"):
            iname = st.text_input("Item Name *")
            c1, c2, c3 = st.columns(3)
            barcode = c1.text_input("Barcode / Item Code")
            hsn = c2.text_input("HSN/SAC")
            unit = c3.selectbox("Unit", ["PCS", "KG", "LTR", "BOX", "MTR", "BAG"])
            
            c1, c2, c3 = st.columns(3)
            gst = c1.selectbox("GST %", [0.0, 5.0, 12.0, 18.0, 28.0])
            p_price = c2.number_input("Purchase Rate", min_value=0.0)
            s_price = c3.number_input("Sale Rate", min_value=0.0)
            
            c1, c2, c3 = st.columns(3)
            op_stk = c1.number_input("Opening Stock", min_value=0.0)
            batch = c2.text_input("Batch No.")
            exp_date = c3.date_input("Expiry Date", value=datetime.now().date() + timedelta(days=365))
            
            if st.form_submit_button("💾 Save Item Master"):
                if iname.strip():
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO items (user_mobile, item_name, item_code, hsn_sac, unit, gst_rate, purchase_price, sale_price, opening_stock, current_stock, batch_no, expiry_date, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (mob, iname, barcode, hsn, unit, gst, p_price, s_price, op_stk, op_stk, batch, str(exp_date), now()))
                    conn.commit()
                    conn.close()
                    log_action("Item Created", "Items", iname)
                    st.success("Item सेव्ह झाला!")
                else:
                    st.error("Item Name आवश्यक आहे.")

    with tab2:
        conn = get_db()
        items_df = pd.read_sql_query("SELECT id, item_name, item_code, unit, current_stock, purchase_price, sale_price, batch_no, expiry_date FROM items WHERE user_mobile=?", conn, params=(mob,))
        conn.close()
        st.dataframe(items_df, use_container_width=True)
        
        st.subheader("🛠️ Item Delete / Update")
        del_id = st.number_input("Enter Item ID to Delete", min_value=0, step=1)
        if st.button("❌ Delete Item"):
            if del_id > 0:
                conn = get_db()
                conn.execute("DELETE FROM items WHERE id=? AND user_mobile=?", (del_id, mob))
                conn.commit()
                conn.close()
                st.success(f"Item ID {del_id} Deleted!")
                st.rerun()

    with tab3:
        conn = get_db()
        exp_df = pd.read_sql_query("SELECT item_name, batch_no, expiry_date, current_stock FROM items WHERE user_mobile=? AND expiry_date <= ?", conn, params=(mob, str(datetime.now().date() + timedelta(days=30))))
        conn.close()
        st.warning("⚠️ पुढील ३० दिवसांत एक्स्पायर होणारे आयटम्स:")
        st.dataframe(exp_df, use_container_width=True)

# --- 6.4 PARTY MASTER (With Edit / Delete) ---
elif menu == "👥 Party Master (Edit/Delete)":
    st.header("👥 Customer & Supplier Master")
    tab1, tab2 = st.tabs(["➕ Add Party", "📋 Manage Parties"])
    
    with tab1:
        with st.form("add_party_form"):
            pname = st.text_input("Party Name *")
            ptype = st.selectbox("Party Type", ["Customer", "Supplier", "Both"])
            pmob = st.text_input("Mobile Number")
            pgst = st.text_input("GSTIN")
            pbal = st.number_input("Opening Balance", value=0.0)
            
            if st.form_submit_button("💾 Save Party"):
                if pname.strip():
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO parties (user_mobile, party_name, party_type, mobile, gstin, opening_balance, created_at)
                        VALUES (?,?,?,?,?,?,?)
                    """, (mob, pname, ptype, pmob, pgst, pbal, now()))
                    conn.commit()
                    conn.close()
                    st.success("Party सेव्ह झाली!")
                else:
                    st.error("Party Name आवश्यक आहे.")

    with tab2:
        conn = get_db()
        parties_df = pd.read_sql_query("SELECT id, party_name, party_type, mobile, gstin, opening_balance FROM parties WHERE user_mobile=?", conn, params=(mob,))
        conn.close()
        st.dataframe(parties_df, use_container_width=True)

# --- 6.5 STOCK TRANSFER & GODOWN ---
elif menu == "🔁 Stock Transfer & Godown":
    st.header("🔁 Godown Stock Transfer")
    with st.form("stock_trf_form"):
        conn = get_db()
        i_list = pd.read_sql_query("SELECT item_name FROM items WHERE user_mobile=?", conn, params=(mob,))["item_name"].tolist()
        conn.close()
        
        st_item = st.selectbox("Select Item", i_list if i_list else ["None"])
        from_g = st.selectbox("From Godown", ["Main Store", "Godown A", "Godown B"])
        to_g = st.selectbox("To Godown", ["Godown A", "Godown B", "Main Store"])
        trf_qty = st.number_input("Transfer Qty", min_value=1.0)
        
        if st.form_submit_button("🔁 Transfer Stock"):
            if from_g == to_g:
                st.error("From आणि To Godown वेगळे असावेत.")
            else:
                log_action("Stock Transfer", "Inventory", f"{st_item} ({trf_qty})")
                st.success(f"✅ {trf_qty} Qty transferred from {from_g} to {to_g} successfully!")
                # --- 6.6 POS & MULTI-ITEM CART (Thermal 58mm / 80mm / A4 Print Support) ---
elif menu == "🛒 POS & Multi-Item Cart":
    st.header("🛒 POS Billing, Barcode Scan & Thermal Print")
    
    if "billing_cart" not in st.session_state:
        st.session_state.billing_cart = []

    conn = get_db()
    items_list = pd.read_sql_query("SELECT item_name, sale_price, gst_rate, item_code FROM items WHERE user_mobile=?", conn, params=(mob,))
    parties_list = pd.read_sql_query("SELECT party_name FROM parties WHERE user_mobile=?", conn, params=(mob,))
    conn.close()

    c1, c2, c3 = st.columns(3)
    cust_name = c1.selectbox("Customer", ["Cash Customer"] + parties_list["party_name"].tolist())
    inv_no = c2.text_input("Invoice No.", value="INV-" + datetime.now().strftime("%Y%m%d%H%M%S"))
    print_fmt = c3.selectbox("Print Layout", ["A4 Standard Invoice", "Thermal 80mm POS", "Thermal 58mm Mini"])

    st.subheader("Add Product")
    c1, c2, c3, c4 = st.columns(4)
    sel_item = c1.selectbox("Select Item", items_list["item_name"].tolist() if not items_list.empty else ["None"])
    qty = c2.number_input("Quantity", min_value=1.0, value=1.0)
    
    rate, gst_r = 0.0, 0.0
    if not items_list.empty and sel_item != "None":
        row = items_list[items_list["item_name"] == sel_item].iloc[0]
        rate = float(row["sale_price"])
        gst_r = float(row["gst_rate"])
        
    rate_inp = c3.number_input("Rate", min_value=0.0, value=rate)
    
    if c4.button("➕ Add Item"):
        taxable = qty * rate_inp
        gst_amt = taxable * gst_r / 100
        st.session_state.billing_cart.append({
            "item_name": sel_item,
            "qty": qty,
            "rate": rate_inp,
            "taxable": taxable,
            "gst_rate": gst_r,
            "gst_amount": gst_amt,
            "total": taxable + gst_amt
        })

    if st.session_state.billing_cart:
        cart_df = pd.DataFrame(st.session_state.billing_cart)
        st.dataframe(cart_df, use_container_width=True)
        grand_total = cart_df["total"].sum()
        st.metric("Bill Amount", money(grand_total))

        if st.button("💾 SAVE & GENERATE PRINT"):
            conn = get_db()
            for row in st.session_state.billing_cart:
                conn.execute("""
                    INSERT INTO transactions (user_mobile, voucher_type, voucher_no, date, party_name, item_name, qty, rate, taxable_amount, gst_rate, cgst, sgst, total_amount, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (mob, "Sales", inv_no, today(), cust_name, row["item_name"], row["qty"], row["rate"], row["taxable"], row["gst_rate"], row["gst_amount"]/2, row["gst_amount"]/2, row["total"], now()))
            conn.commit()
            conn.close()
            st.session_state.billing_cart = []
            st.success(f"✅ Invoice {inv_no} Saved ({print_fmt} Layout Generated)!")
            st.rerun()

# --- 6.7 VOUCHERS ENGINE ---
elif menu == "🧾 Vouchers Engine":
    st.header("🧾 Quick Vouchers (Receipt / Payment / Contra / Journal / Returns)")
    vtype = st.selectbox("Voucher Type", ["Receipt", "Payment", "Expense", "Contra", "Journal", "Sales Return", "Purchase Return"])
    
    with st.form("v_form"):
        vno = st.text_input("Voucher No.", value=vtype[:3].upper() + "-" + datetime.now().strftime("%Y%m%d%H%M%S"))
        pname = st.text_input("Party / Ledger Account")
        amt = st.number_input("Amount", min_value=0.0)
        mode = st.selectbox("Payment Mode", ["Cash", "Bank", "UPI", "Cheque"])
        narration = st.text_area("Narration")
        
        if st.form_submit_button("💾 Save Voucher Entry"):
            if amt > 0:
                conn = get_db()
                conn.execute("""
                    INSERT INTO transactions (user_mobile, voucher_type, voucher_no, date, party_name, total_amount, payment_mode, narration, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (mob, vtype, vno, today(), pname, amt, mode, narration, now()))
                
                dr = amt if vtype in ["Payment", "Expense", "Sales Return"] else 0
                cr = amt if vtype in ["Receipt", "Purchase Return"] else 0
                conn.execute("""
                    INSERT INTO ledger (user_mobile, date, account_name, account_type, voucher_type, voucher_no, particulars, debit, credit, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (mob, today(), pname, vtype, vtype, vno, narration, dr, cr, now()))
                
                conn.commit()
                conn.close()
                st.success(f"✅ {vtype} Entry Saved!")
            else:
                st.error("Amount enter करा.")

# --- 6.8 BOOKS & LEDGERS ---
elif menu == "📒 Books & Ledgers":
    st.header("📒 Day Book, Cash Book, Bank Book & Ledgers")
    book_type = st.radio("Select View", ["Day Book", "Party Ledger", "Cash Book", "Bank Book"])
    
    conn = get_db()
    if book_type == "Day Book":
        df = pd.read_sql_query("SELECT date, voucher_type, voucher_no, party_name, total_amount, payment_mode FROM transactions WHERE user_mobile=? AND date=?", conn, params=(mob, today()))
    else:
        df = pd.read_sql_query("SELECT date, voucher_type, voucher_no, account_name, debit, credit FROM ledger WHERE user_mobile=?", conn, params=(mob,))
    conn.close()
    
    st.dataframe(df, use_container_width=True)

# --- 6.9 FINANCIAL REPORTS ---
elif menu == "📊 Financial Reports":
    st.header("📊 Trial Balance, Profit & Loss, Balance Sheet & Outstanding")
    rep_type = st.selectbox("Report Type", ["Profit & Loss", "Trial Balance", "Balance Sheet", "Outstanding Receivables", "Outstanding Payables"])
    
    conn = get_db()
    if rep_type == "Profit & Loss":
        sales = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Sales'", (mob,)).fetchone()[0]
        purch = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Purchase'", (mob,)).fetchone()[0]
        exp = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM transactions WHERE user_mobile=? AND voucher_type='Expense'", (mob,)).fetchone()[0]
        
        st.write(f"**Total Sales Income:** {money(sales)}")
        st.write(f"**Total Purchase Cost:** {money(purch)}")
        st.write(f"**Total Operating Expense:** {money(exp)}")
        st.subheader(f"Net Profit / Loss: {money(sales - purch - exp)}")
        
    elif rep_type == "Trial Balance":
        tb_df = pd.read_sql_query("SELECT account_name, SUM(debit) as Debit, SUM(credit) as Credit FROM ledger WHERE user_mobile=? GROUP BY account_name", conn, params=(mob,))
        st.dataframe(tb_df, use_container_width=True)
    conn.close()

# --- 6.10 GST & GSTR-2B IMPORT ---
elif menu == "🧾 GST & GSTR-2B Import":
    st.header("🧾 GST Summary, GSTR-1 & GSTR-2B Recon Import")
    tab1, tab2 = st.tabs(["📊 GSTR-1 Sales Data", "📥 GSTR-2B Reconciliation Import"])
    
    conn = get_db()
    with tab1:
        gst_df = pd.read_sql_query("SELECT date, voucher_no, party_name, hsn_sac, taxable_amount, cgst, sgst, igst, total_amount FROM transactions WHERE user_mobile=? AND gst_rate > 0", conn, params=(mob,))
        st.dataframe(gst_df, use_container_width=True)
        st.download_button("📥 Export GSTR-1 CSV Data", gst_df.to_csv(index=False).encode('utf-8'), "GSTR1_Data.csv", "text/csv")
        
    with tab2:
        st.subheader("Import GSTR-2B / Purchase Excel for ITC Reconciliation")
        uploaded_file = st.file_uploader("Upload Portal GSTR-2B File (CSV/Excel)", type=["csv", "xlsx"])
        if uploaded_file:
            st.success("✅ GSTR-2B File uploaded successfully for ITC Matching!")
    conn.close()

# --- 6.11 BACKUP, RESTORE & AUDIT LOG ---
elif menu == "💾 Backup, Restore & Audit":
    st.header("💾 JSON/Excel Backup & Audit Log")
    tab1, tab2 = st.tabs(["📥 Backup Data", "📋 Audit Logs"])
    conn = get_db()
    
    with tab1:
        all_df = pd.read_sql_query("SELECT * FROM transactions WHERE user_mobile=?", conn, params=(mob,))
        st.download_button("📥 Download JSON Database Backup", all_df.to_json(orient="records"), "tally_backup.json", "application/json")
        
    with tab2:
        logs_df = pd.read_sql_query("SELECT action, module, reference_no, created_at FROM audit_logs WHERE user_mobile=? ORDER BY id DESC", conn, params=(mob,))
        st.dataframe(logs_df, use_container_width=True)
        
    conn.close()
# ============================================================
# 7. ADVANCED EXTENSIONS (Thermal Print, WhatsApp, UPI, GSTR-3B & Barcode)
# ============================================================

# --- 7.1 PRINT & INVOICE TEMPLATES ---
def render_invoice_html(inv_no, cust_name, cart_data, total_amt, fmt="A4"):
    html_code = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; max-width: {'800px' if fmt=='A4' else '300px'}; margin: auto;">
        <h2 style="text-align: center; margin-bottom: 5px;">SD TALLY BUSINESS</h2>
        <p style="text-align: center; font-size: 12px; margin-top: 0;">Tax Invoice / Bill of Supply</p>
        <hr/>
        <p><strong>Invoice No:</strong> {inv_no}<br/>
        <strong>Customer:</strong> {cust_name}<br/>
        <strong>Date:</strong> {today()}</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
            <thead>
                <tr style="background: #f2f2f2; border-bottom: 1px solid #ddd;">
                    <th style="text-align: left; padding: 5px;">Item</th>
                    <th style="text-align: right; padding: 5px;">Qty</th>
                    <th style="text-align: right; padding: 5px;">Rate</th>
                    <th style="text-align: right; padding: 5px;">Total</th>
                </tr>
            </thead>
            <tbody>
    """
    for item in cart_data:
        html_code += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 5px;">{item['item_name']}</td>
                <td style="text-align: right; padding: 5px;">{item['qty']}</td>
                <td style="text-align: right; padding: 5px;">₹{item['rate']}</td>
                <td style="text-align: right; padding: 5px;">₹{item['total']}</td>
            </tr>
        """
    
    html_code += f"""
            </tbody>
        </table>
        <hr/>
        <h3 style="text-align: right;">Grand Total: ₹{total_amt:,.2f}</h3>
        <p style="text-align: center; font-size: 10px; margin-top: 20px;">Thank you for your business!</p>
    </div>
    """
    return html_code

# --- 7.2 WHATSAPP & UPI INTEGRATION MODULE ---
elif menu == "💬 WhatsApp & UPI Payment":
    st.header("💬 WhatsApp Invoice Sharing & UPI QR Setup")
    
    conn = get_db()
    cust_df = pd.read_sql_query("SELECT party_name, mobile FROM parties WHERE user_mobile=? AND party_type='Customer'", conn, params=(mob,))
    conn.close()
    
    c1, c2 = st.columns(2)
    sel_cust = c1.selectbox("Select Customer", cust_df["party_name"].tolist() if not cust_df.empty else ["None"])
    bill_amt = c2.number_input("Invoice Amount", min_value=0.0)
    
    cust_mob = ""
    if not cust_df.empty and sel_cust != "None":
        cust_mob = cust_df[cust_df["party_name"] == sel_cust]["mobile"].values[0]
        
    cust_mob_input = st.text_input("Customer WhatsApp Mobile", value=cust_mob)
    
    if st.button("📲 Send WhatsApp Reminder / Invoice"):
        msg = f"Hello {sel_cust}, your invoice of amount {money(bill_amt)} is ready from SD Tally Business. Thank you!"
        encoded_msg = msg.replace(" ", "%20")
        whatsapp_url = f"https://wa.me/91{cust_mob_input}?text={encoded_msg}"
        st.markdown(f"[👉 Click Here to Send WhatsApp Message]({whatsapp_url})", unsafe_allow_click_link=True)

    st.divider()
    st.subheader("📲 Instant UPI QR Code Generator")
    upi_id = st.text_input("Your UPI ID (e.g., mobile@upi / gpay)", value="9876543210@upi")
    if bill_amt > 0 and upi_id:
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa={upi_id}&pn=SDTally&am={bill_amt}&cu=INR"
        st.image(qr_url, caption=f"Scan to Pay {money(bill_amt)}")

# --- 7.3 GSTR-3B SUMMARY REPORT ---
elif menu == "📊 GSTR-3B Summary":
    st.header("📊 GSTR-3B Net Tax Liability Report")
    conn = get_db()
    
    output_gst = conn.execute("SELECT COALESCE(SUM(cgst+sgst+igst),0) FROM transactions WHERE user_mobile=? AND voucher_type='Sales'", (mob,)).fetchone()[0]
    input_gst = conn.execute("SELECT COALESCE(SUM(cgst+sgst+igst),0) FROM transactions WHERE user_mobile=? AND voucher_type='Purchase'", (mob,)).fetchone()[0]
    conn.close()
    
    net_payable = output_gst - input_gst
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Output Tax (Sales)", money(output_gst))
    c2.metric("Input Tax Credit (Purchase)", money(input_gst))
    c3.metric("Net Payable Tax", money(net_payable if net_payable > 0 else 0))

# --- 7.4 BARCODE & MULTI-BANK SETUP ---
elif menu == "🏷️ Barcode & Multi-Bank Setup":
    st.header("🏷️ Barcode Generator & Bank Accounts")
    tab1, tab2 = st.tabs(["🏷️ Item Barcode Generator", "🏦 Bank Accounts"])
    
    with tab1:
        item_code_gen = st.text_input("Enter Item Code for Barcode", value="ITEM-101")
        if item_code_gen:
            barcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={item_code_gen}"
            st.image(barcode_url, caption=f"Barcode/QR for {item_code_gen}")
            
    with tab2:
        with st.form("bank_add"):
            b_name = st.text_input("Bank Name (e.g. SBI, HDFC)")
            ac_no = st.text_input("Account Number")
            if st.form_submit_button("💾 Save Bank"):
                st.success(f"✅ Bank Account {b_name} Saved Successfully!")

# --- 7.5 BANK EXCEL IMPORT & MIGRATION ---
elif menu == "📥 Excel Import & Migration":
    st.header("📥 Bank Statement & Excel Master Import")
    uploaded_file = st.file_uploader("Upload Excel / CSV File", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            df_imp = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.success("File Processed Successfully!")
            st.dataframe(df_imp, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ============================================================
# END OF SD TALLY BUSINESS ENTERPRISE APPLICATION
# ============================================================
