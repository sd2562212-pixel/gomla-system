import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. إعداد واجهة النظام والتسمية
st.set_page_config(page_title="سيستم محل الجملة الشامل والمطور", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>سيستم محل الجملة الشامل 🛒</h1>", unsafe_allow_html=True)

# 2. الاتصال بقاعدة البيانات (نفس قاعدة بيانات تطبيق Streamlit الخاص بك)
conn = sqlite3.connect('gomla_shop_v1_ultimate_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, today_price REAL, stock INTEGER, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS customers 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS daily_price_snapshot 
    (product_name TEXT, price REAL, snapshot_date TEXT, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_type TEXT, party_name TEXT, product_name TEXT, quantity INTEGER, total_amount REAL)''')
conn.commit()

# 3. إدارة جلسة المستخدم (Session State)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# 4. بوابة تسجيل الدخول / إنشاء الحساب
if not st.session_state.logged_in:
    auth_mode = st.radio("اختر العملية المراد القيام بها", ["تسجيل دخول بحساب سابق 🔑", "إنشاء حساب جديد للمحل ➕"], horizontal=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    if auth_mode == "إنشاء حساب جديد للمحل ➕":
        st.markdown("<h3 style='text-align: center; color: #4CAF50;'>إنشاء حساب جديد للمحل 👤</h3>", unsafe_allow_html=True)
        new_email = st.text_input("البريد الإلكتروني الجديد (Email)", key="reg_email").strip().lower()
        new_password = st.text_input("اختر كلمة المرور (Password)", type="password", key="reg_pass")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="reg_confirm")
        
        if st.button("تفعيل وإنشاء الحساب ✔️", use_container_width=True):
            if new_email and new_password:
                if new_password == confirm_password:
                    try:
                        cursor.execute("INSERT INTO users VALUES (?, ?)", (new_email, new_password))
                        conn.commit()
                        st.success("تم إنشاء الحساب بنجاح! انتقل الآن لتبويب 'تسجيل دخول بحساب سابق' للدخول 🎉")
                    except sqlite3.IntegrityError:
                        st.error("⚠️ هذا البريد الإلكتروني مسجل بالفعل بالنظام من قبل!")
                else:
                    st.error("❌ كلمات المرور غير متطابقة")
            else:
                st.error("⚠️ برجاء ملء جميع الخانات")
                
    elif auth_mode == "تسجيل دخول بحساب سابق 🔑":
        st.markdown("<h3 style='text-align: center; color: #1E88E5;'>تسجيل دخول النظام المشترك 🔐</h3>", unsafe_allow_html=True)
        email_input = st.text_input("البريد الإلكتروني (Email)", key="log_email").strip().lower()
        password_input = st.text_input("كلمة المرور (Password)", type="password", key="log_pass")
        
        if st.button("دخول ومزامنة الأجهزة ⚡", use_container_width=True):
            if email_input and password_input:
                cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email_input, password_input))
                if cursor.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة!")
            else:
                st.error("⚠️ برجاء إدخال البيانات المطلوبة")

# 5. لوحة التحكم الرئيسية بعد تسجيل الدخول الصحيح
else:
    user_email = st.session_state.user_email
    
    col_user, col_logout = st.columns(2)
    with col_user:
        st.write(f"👤 الحساب النشط: **{user_email}**")
    with col_logout:
        if st.button("تسجيل الخروج 🚪"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
            
    st.markdown("---")
    
    # تبويب إدارة المنتجات وحذفها (مكان حدوث الخطأ القديم)
    st.subheader("🛠️ إدارة السلع والمنتجات")
    
    # جلب البيانات الحالية من جدول المنتجات
    prod_data = pd.read_sql_query("SELECT * FROM products", conn)
    
    if not prod_data.empty:
        # هنا تم الإصلاح: نستخدم 'id' أو 'name' بدلاً من كلمة 'الكود' باللغة العربية
        # قمنا بدمج الرقم مع الاسم ليختار المستخدم بشكل أسهل
        prod_data['display_name'] = prod_data['id'].astype(str) + " - " + prod_data['name']
        
        options_list = prod_data['display_name'].dropna().unique().tolist()
        
        # أداة الاختيار بعد التعديل لتجنب الـ TypeError تماماً
        selected_option = st.selectbox("اختر السلعة للحذف النهائي 🗑️", options=options_list)
        
        if st.button("تأكيد الحذف النهائي ❌", type="primary"):
            # استخراج الـ ID الفعلي من الخيار المختار
            selected_id = selected_option.split(" - ")[0]
            
            cursor.execute("DELETE FROM products WHERE id = ?", (selected_id,))
            conn.commit()
            st.success("تم حذف السلعة بنجاح!")
            st.rerun()
    else:
        st.info("📦 لا توجد سلع مضافة حالياً في قاعدة البيانات.")
