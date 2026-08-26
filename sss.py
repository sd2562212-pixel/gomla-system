import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي للموبايل والكمبيوتر
st.set_page_config(page_title="سيستم محل الجملة الشامل", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🚀 سيستم محل الجملة الشامل</h1>", unsafe_allow_html=True)

# الاتصال بقاعدة البيانات السحابية المشتركة بين الأجهزة
conn = sqlite3.connect('gomla_shared_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول الشاملة للنظام
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    (id INTEGER PRIMARY KEY, name TEXT, type TEXT, balance REAL)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS price_history 
    (product_name TEXT, price REAL, date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
    (id INTEGER PRIMARY KEY, account_name TEXT, total REAL, date TEXT, type TEXT)''')

# إضافة بضاعة تجريبية للمخزن إذا كان فارغاً
cursor.execute("SELECT count(*) FROM products")
if cursor.fetchone() == 0:
    cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock) VALUES ('طن دقيق الهدى', 14000, 15000, 50)")
    cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock) VALUES ('كرتونة زيت سلايت', 650, 700, 100)")
    conn.commit()

# قائمة التنقل العلوية المريحة للموبايل
menu = ft = st.tabs(["📊 أسعار اليوم", "👥 الديون والحسابات", "🧾 الفواتير والمخزن"])

# --- 1. شاشة تحديث الأسعار اليومية ---
with menu[0]:
    st.subheader("تحديث أسعار السلع لحظياً")
    products = pd.read_sql_query("SELECT * FROM products", conn)
    
    for index, row in products.iterrows():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"✨ **{row['name']}**\n(سعر الشراء: {row['purchase_price']} ج.م | المخزن: {row['stock']})")
        with col2:
            new_price = st.number_input(f"سعر البيع اليوم", value=float(row['today_price']), key=f"p_{row['id']}")
            
        if new_price != row['today_price']:
            cursor.execute("UPDATE products SET today_price = ? WHERE id = ?", (new_price, row['id']))
            cursor.execute("INSERT INTO price_history VALUES (?, ?, ?)", (row['name'], new_price, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            st.toast(f"✅ تم تحديث سعر {row['name']} على جميع الأجهزة!")

# --- 2. شاشة الديون والحسابات (الداين والمدين) ---
with menu[1]:
    st.subheader("دفتر ديون العملاء والموردين")
    
    with st.expander("➕ إضافة عميل أو مورد جديد للدفتر"):
        name = st.text_input("اسم الشخص أو المحل")
        acc_type = st.selectbox("نوع الحساب", ["عميل (مدين - عليه فلوس)", "مورد (دائن - يطلب فلوس)"])
        balance = st.number_input("الحساب الحالي الإجمالي (ج.م)", value=0.0)
        if st.button("حفظ الحساب في الدفتر"):
            if name:
                cursor.execute("INSERT INTO accounts (name, type, balance) VALUES (?, ?, ?)", (name, acc_type, balance))
                conn.commit()
                st.success(f"تم تسجيل {name} بنجاح!")
                st.rerun()

    # عرض الحسابات الإجمالية للعملاء والموردين
    st.markdown("### 📋 قائمة الحسابات الحالية")
    accounts_df = pd.read_sql_query("SELECT name as 'الاسم', type as 'النوع', balance as 'الحساب الحالي (ج.م)' FROM accounts", conn)
    st.dataframe(accounts_df, use_container_width=True)

# --- 3. شاشة الفواتير والمخزن وأرشيف الأسعار ---
with menu[2]:
    st.subheader("📦 حالة المخزن الحالي")
    products_df = pd.read_sql_query("SELECT name as 'السلعة', today_price as 'سعر اليوم', stock as 'الكمية المتبقية' FROM products", conn)
    st.table(products_df)
    
    st.subheader("📈 أرشيف حركات الأسعار اليومية")
    history_df = pd.read_sql_query("SELECT product_name as 'السلعة', price as 'السعر المسجل', date as 'التاريخ والوقت' FROM price_history ORDER BY date DESC", conn)
    st.dataframe(history_df, use_container_width=True)
