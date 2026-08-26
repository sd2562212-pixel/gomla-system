import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام البسيطة والواضحة
st.set_page_config(page_title="سيستم محل الجملة - النسخة الأولى النظيفة", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🚀 سيستم محل الجملة الشامل</h1>", unsafe_allow_html=True)

# الاتصال بقاعدة البيانات المحلية المشتركة تلقائياً
conn = sqlite3.connect('gomla_shop_v1_clean_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول الأساسية المباشرة للنظام
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, balance REAL)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS price_history 
    (product_name TEXT, price REAL, date TEXT)''')

conn.commit()

# قائمة التنقل العلوية المريحة جداً للموبايل
tab1, tab2, tab3 = st.tabs(["📊 أسعار اليوم", "👥 الديون والحسابات", "📦 المخزن والسلع الجديد"])

# --- 1. شاشة تحديث الأسعار اليومية السريعة ---
with tab1:
    st.subheader("تحديث أسعار السلع لحظياً")
    products = pd.read_sql_query("SELECT * FROM products", conn)
    
    if products.empty:
        st.info("💡 لا توجد سلع مضافة حالياً. اذهب لتبويب 'المخزن والسلع الجديدة' لإضافة أول صنف لمحلك.")
    else:
        for index, row in products.iterrows():
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"✨ **{row['name']}**\n\n(سعر الشراء: {row['purchase_price']} ج.م | المخزن: {row['stock']})")
            with col2:
                new_price = st.number_input(f"سعر البيع اليوم", value=float(row['today_price']), key=f"p_{row['id']}")
                
            if new_price != row['today_price']:
                cursor.execute("UPDATE products SET today_price = ? WHERE id = ?", (new_price, row['id']))
                cursor.execute("INSERT INTO price_history VALUES (?, ?, ?)", (row['name'], new_price, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.toast(f"✅ تم تحديث سعر {row['name']} على جميع الأجهزة!")
                st.rerun()

# --- 2. شاشة الديون والحسابات (الداين والمدين) ---
with tab2:
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

    st.markdown("### 📋 قائمة الحسابات الحالية")
    accounts_df = pd.read_sql_query("SELECT name as 'الاسم', type as 'النوع', balance as 'الحساب الحالي (ج.م)' FROM accounts", conn)
    st.dataframe(accounts_df, use_container_width=True)

# --- 3. شاشة إدارة المخزن والسلع الجديدة وأرشيف حركات الأسعار ---
with tab3:
    st.subheader("➕ إضافة صنف/بضاعة جديدة للمخزن")
    new_p_name = st.text_input("اسم السلعة (مثال: طن أرز الفيروز)")
    new_p_purchase = st.number_input("سعر التكلفة/الشراء الأساسي (ج.م)", value=0.0)
    new_p_today = st.number_input("سعر البيع لليوم (ج.م)", value=0.0)
    new_p_stock = st.number_input("الكمية المتوفرة بالمخزن", value=0, step=1)
    
    if st.button("حفظ السلعة بالمخزن المشترك"):
        if new_p_name:
            cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock) VALUES (?, ?, ?, ?)", 
                           (new_p_name, new_p_purchase, new_p_today, new_p_stock))
            conn.commit()
            st.success(f"تمت إضافة {new_p_name} للمخزن بنجاح!")
            st.rerun()
            
    st.markdown("---")
    st.subheader("📦 حالة المخزن وجرد الكميات الحالي")
    products_df = pd.read_sql_query("SELECT name as 'السلعة', today_price as 'سعر اليوم', stock as 'الكمية المتبقية' FROM products", conn)
    st.table(products_df)
    
    st.subheader("📈 أرشيف حركات تعديل الأسعار")
    history_df = pd.read_sql_query("SELECT product_name as 'السلعة', price as 'السعر المسجل', date as 'التاريخ والوقت' FROM price_history ORDER BY date DESC", conn)
    st.dataframe(history_df, use_container_width=True)
