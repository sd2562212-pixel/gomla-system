
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي الحديثة جداً
st.set_page_config(page_title="منظومة الإدارة المالية الذكية", layout="centered")

# تصميم بصري متطور جداً (Premium Dark-Tech UI)
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B; border-radius: 10px; padding: 12px 24px; color: #94A3B8; font-weight: bold; font-size: 15px;
    }
    .stTabs [aria-selected="true"] { background-color: #2563EB !important; color: white !important; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
    .main-card {
        background-color: #0F172A; padding: 20px; border-radius: 12px; 
        border-left: 5px solid #3B82F6; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .alert-card {
        background-color: #7C2D12; padding: 12px; border-radius: 8px; border-right: 5px solid #EA580C; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# الحل الجذري: الاتصال بقاعدة بيانات جديدة كلياً لتفادي تضارب القوائم والجداول القديمة
conn = sqlite3.connect('gomla_perfect_v12_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الهيكل المحاسبي الشامل والمتطور للمحل
cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS customers 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS daily_price_snapshot 
    (product_name TEXT, price REAL, snapshot_date TEXT, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_type TEXT, party_name TEXT, product_name TEXT, quantity INTEGER, total_amount REAL, profit REAL, date TEXT, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS cash_flow 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, party_name TEXT, amount REAL, date TEXT, user_email TEXT)''')

conn.commit()

# --- إدارة جلسة تسجيل الدخول (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 1. بوابة الأمان المشتركة لتسجيل الدخول ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #2563EB; font-weight: 800; margin-bottom:10px;'>📊 منظومة الجملة الذكية</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>نظام ربط ومزامنة هواتف المحل والمخازن لحظياً</p>", unsafe_allow_html=True)
    
    auth_mode = st.radio("اختر العملية المطلوبة:", ["🔑 تسجيل دخول بحساب سابق", "➕ إنشاء حساب جديد للمحل"], horizontal=True)
    st.markdown("<hr style='margin:15px 0; border-color: #334155;'>", unsafe_allow_html=True)

    if auth_mode == "➕ إنشاء حساب جديد للمحل":
        st.markdown("<h3 style='text-align: center; color: #10B981;'>📝 تسجيل بيانات المحل لأول مرة</h3>", unsafe_allow_html=True)
        new_email = st.text_input("البريد الإلكتروني للمحل (Email)").strip().lower()
        new_password = st.text_input("اختر كلمة مرور قوية (Password)", type="password")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password")
        
        if st.button("🚀 تفعيل الحساب السحابي المشترك", use_container_width=True):
            if new_email and new_password:
                if new_password == confirm_password:
                    try:
                        cursor.execute("INSERT INTO users VALUES (?, ?)", (new_email, new_password))
                        conn.commit()
                        st.success("🎉 تم إنشاء الحساب بنجاح! انتقل الآن لتبويب 'تسجيل دخول بحساب سابق' للبدء.")
                    except sqlite3.IntegrityError:
                        st.error("⚠️ هذا الحساب مسجل لدينا بالفعل!")
                else:
                    st.error("❌ كلمات المرور غير متطابقة")
            else:
                st.error("برجاء ملء كافة الخانات")

    elif auth_mode == "🔑 تسجيل دخول بحساب سابق":
        st.markdown("<h3 style='text-align: center; color: #2563EB;'>🔐 تسجيل دخول النظام المشترك</h3>", unsafe_allow_html=True)
        email_input = st.text_input("البريد الإلكتروني (Email)").strip().lower()
        password_input = st.text_input("كلمة المرور (Password)", type="password")
        
        if st.button("⚡ دخول ومزامنة كافة الهواتف", use_container_width=True):
            if email_input and password_input:
                cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email_input, password_input))
                if cursor.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ الحساب غير موجود أو كلمة المرور خاطئة!")
            else:
                st.error("برجاء إدخال البيانات المطلوبة")

# --- 2. لوحة التحكم الاحترافية (بعد الدخول الصحيح) ---
else:
    user_email = st.session_state.user_email
    
    col_user, col_logout = st.columns(2)
    with col_user:
        st.markdown(f"✨ **المنظومة متصلة ومزامنة:** `{user_email}`")
    with col_logout:
        if st.button("🔒 خروج آمن", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
            
    st.markdown("<hr style='margin-top:0; margin-bottom:20px; border-color: #334155;'>", unsafe_allow_html=True)

    # حساب مؤشرات الأداء والتحكم
    cursor.execute("SELECT COUNT(*) FROM products WHERE user_email=?", (user_email,))
    total_items = cursor.fetchone()[0]
    cursor.execute("SELECT IFNULL(SUM(balance), 0) FROM customers WHERE user_email=?", (user_email,))
    total_cust_deb = cursor.fetchone()[0]
    cursor.execute("SELECT IFNULL(SUM(profit), 0) FROM invoices WHERE user_email=?", (user_email,))
    total_profits = cursor.fetchone()[0]

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="📦 أصناف المخزن", value=f"{total_items} صنف")
    with m2:
        st.metric(label="🔴 ديون العملاء بالسوق", value=f"{total_cust_deb:,.1f} ج.م")
    with m3:
        st.metric(label="💰 صافي الأرباح", value=f"{total_profits:,.1f} ج.م")

    # تنبيهات نقص المخزن
    cursor.execute("SELECT name, stock FROM products WHERE user_email=? AND stock <= 5", (user_email,))
    low_stock_items = cursor.fetchall()
    if low_stock_items:
        st.markdown("<br>", unsafe_allow_html=True)
        for item in low_stock_items:
            st.markdown(f"<div class='alert-card'>⚠️ <b>تنبيه مخزن:</b> صنف (<b>{item[0]}</b>) أوشك على النفاد! المتبقي: {item[1]} قطعة.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📦 المخزن وجرد الأسعار", "👥 حسابات السوق والديون", "🧾 حركة الفواتير والتحصيل", "📅 أرشيف السجلات والتاريخ"])

    # --- التبويب الأول: إدارة المخزن الشامل وجدول الإكسيل التفاعلي ---
    with tab1:
        st.markdown("<h4>📦 مستودع السلع وتحديث الأسعار التفاعلي</h4>", unsafe_allow_html=True)
        
        with st.expander("➕ إضافة سلعة جديدة للمخزن الأصلي"):
            p_name = st.text_input("اسم السلعة (مثال: طن دقيق الهدى)")
            p_purchase = st.number_input("سعر تكلفة الشراء الأساسي (مخفي للربح) - ج.م", value=None, placeholder="اكتب سعر الشراء لخصم الأرباح...")
            p_today = st.number_input("سعر بيع اليوم الافتتاحي - ج.م", value=None, placeholder="اكتب سعر البيع...")
            p_stock = st.number_input("إجمالي الكمية المتوفرة حالياً", value=None, placeholder="اكتب كمية المخزن بالعدد...", step=1)
            
            if st.button("💾 حفظ الصنف الجديد سحابياً", use_container_width=True):
                if p_name and p_purchase is not None and p_today is not None and p_stock is not None:
                    cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock, user_email) VALUES (?, ?, ?, ?, ?)", (p_name, p_purchase, p_today, p_stock, user_email))
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO daily_price_snapshot VALUES (?, ?, ?, ?)", (p_name, p_today, today_str, user_email))
                    conn.commit()
                    st.success(f"✅ تم تسجيل {p_name} بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ برجاء ملء كافة الخانات وتحديد البيانات بدقة!")

        st.markdown("---")
        st.subheader("📋 جدول إكسيل التفاعلي لجرد السلع")
        
        prod_data = pd.read_sql_query("SELECT id, name, today_price, stock FROM products WHERE user_email = ?", conn)
        
        if not prod_data.empty:
            prod_data.columns = ['الكود', 'اسم السلعة 📦', 'سعر البيع ج.م 💰', 'الكمية المتاحة حالياً 🧮']
            edited_df = st.data_editor(prod_data, hide_index=True, use_container_width=True, disabled=["الكود", "اسم السلعة 📦"])
            
            for idx, row in edited_df.iterrows():
                old_row = prod_data.iloc[idx]
                if row['سعر البيع ج.م 💰'] != old_row['سعر البيع ج.م 💰'] or row['الكمية المتاحة حالياً 🧮'] != old_row['الكمية المتاحة حالياً 🧮']:
                    cursor.execute("UPDATE products SET today_price = ?, stock = ? WHERE id = ? AND user_email = ?", (row['سعر البيع ج.م 💰'], row['الكمية المتاحة حالياً 🧮'], row['الكود'], user_email))
                    today_str = datetime.now().strftime("%Y-%m-%d")
