import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي
st.set_page_config(page_title="سيستم محل الجملة الذكي المتكامل", layout="centered")

# الاتصال بقاعدة بيانات جديدة ونظيفة لضمان استقرار العمل
conn = sqlite3.connect('gomla_perfect_final_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء وتحديث الجداول المحاسبية المتطورة
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
    (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_type TEXT, party_name TEXT, product_name TEXT, quantity INTEGER, total_amount REAL, date TEXT, user_email TEXT)''')

conn.commit()

# --- إدارة جلسة تسجيل الدخول (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 1. شاشات الحسابات الموحدة وبوابة الحماية ---
if not st.session_state.logged_in:
    auth_mode = st.radio("اختر العملية المراد القيام بها:", ["🔑 تسجيل دخول بحساب سابق", "➕ إنشاء حساب جديد للمحل"], horizontal=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    if auth_mode == "➕ إنشاء حساب جديد للمحل":
        st.markdown("<h3 style='text-align: center; color: #4CAF50;'>📝 إنشاء حساب جديد للمحل</h3>", unsafe_allow_html=True)
        new_email = st.text_input("البريد الإلكتروني الجديد (Email)", key="reg_email").strip().lower()
        new_password = st.text_input("اختر كلمة المرور (Password)", type="password", key="reg_pass")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="reg_confirm")
        
        if st.button("تأكيد وإنشاء الحساب الحركي", use_container_width=True):
            if new_email and new_password:
                if new_password == confirm_password:
                    try:
                        cursor.execute("INSERT INTO users VALUES (?, ?)", (new_email, new_password))
                        conn.commit()
                        st.success("🎉 تم إنشاء الحساب بنجاح! انتقل الآن لتبويب 'تسجيل دخول بحساب سابق' للدخول.")
                    except sqlite3.IntegrityError:
                        st.error("⚠️ هذا البريد الإلكتروني مسجل بالفعل بالنظام من قبل!")
                else:
                    st.error("❌ كلمات المرور غير متطابقة")
            else:
                st.error("برجاء ملء جميع الخانات")

    elif auth_mode == "🔑 تسجيل دخول بحساب سابق":
        st.markdown("<h3 style='text-align: center; color: #1E88E5;'>🔐 تسجيل دخول النظام المشترك</h3>", unsafe_allow_html=True)
        email_input = st.text_input("البريد الإلكتروني (Email)", key="log_email").strip().lower()
        password_input = st.text_input("كلمة المرور (Password)", type="password", key="log_pass")
        
        if st.button("دخول ومزامنة الأجهزة", use_container_width=True):
            if email_input and password_input:
                cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email_input, password_input))
                if cursor.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ البيانات غير صحيحة!")
            else:
                st.error("برجاء إدخال البيانات المطلوبة")

# --- 2. لوحة التحكم الرئيسية بعد تسجيل الدخول الصحيح ---
else:
    user_email = st.session_state.user_email
    
    col_user, col_logout = st.columns(2)
    with col_user:
        st.markdown(f"🟢 **متصل ومزامن:** `{user_email}`")
    with col_logout:
        if st.button("خروج آمن"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
            
    st.markdown("<hr style='margin-top:0; margin-bottom:15px;'>", unsafe_allow_html=True)

    # التبويبات المحاسبية المتطورة
    tab1, tab2, tab3, tab4 = st.tabs(["📦 إدارة السلع والمخزن", "👥 الموردين والعملاء", "🧾 تسجيل الفواتير الذكي", "📅 المرجعيات والأرشيف التاريخي"])

    # --- التبويب الأول: إدارة المخزن والأسعار الحالية وحفظ اللقطة اليومية ---
    with tab1:
        st.subheader("🏬 مستودع البضائع والأسعار الحالية")
        
        with st.expander("➕ إضافة سلعة جديدة للمخزن"):
            p_name = st.text_input("اسم السلعة الجديد")
            p_today = st.number_input("سعر البيع الحالي (ج.م)", value=None, placeholder="اكتب سعر البيع...")
            p_stock = st.number_input("الكمية المتاحة حالياً بالمخزن", value=None, placeholder="اكتب كمية المخزن الأولية...", step=1)
            
            if st.button("حفظ السلعة"):
                if p_name and p_today is not None and p_stock is not None:
                    cursor.execute("INSERT INTO products (name, today_price, stock, user_email) VALUES (?, ?, ?, ?)", (p_name, p_today, p_stock, user_email))
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO daily_price_snapshot VALUES (?, ?, ?, ?)", (p_name, p_today, today_str, user_email))
                    conn.commit()
                    st.success(f"تم تسجيل {p_name} بالمخزن وتثبيت سعرها!")
                    st.rerun()
                else:
                    st.error("❌ برجاء ملء كافة الخانات أولاً!")
                    
        st.markdown("---")
        st.subheader("📋 قائمة جرد المخزن وتحديث الأسعار المستمرة")
        
        try:
            prod_data = pd.read_sql_query("SELECT id, name, today_price, stock FROM products WHERE user_email = ?", conn)
        except:
            prod_data = pd.DataFrame(columns=['id', 'name', 'today_price', 'stock'])
        
        if not prod_data.empty:
            prod_data.columns = ['id', 'اسم السلعة', 'سعر البيع ج.م', 'الكمية الحالية']
            edited_df = st.data_editor(prod_data, hide_index=True, use_container_width=True, disabled=["id", "اسم السلعة"])
            
            for idx, row in edited_df.iterrows():
                old_row = prod_data.iloc[idx]
                if row['سعر البيع ج.م'] != old_row['سعر البيع ج.م'] or row['الكمية الحالية'] != old_row['الكمية الحالية']:
                    cursor.execute("UPDATE products SET today_price = ?, stock = ? WHERE id = ? AND user_email = ?", (row['سعر البيع ج.م'], row['الكمية الحالية'], row['id'], user_email))
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("DELETE FROM daily_price_snapshot WHERE product_name = ? AND snapshot_date = ? AND user_email = ?", (row['اسم السلعة'], today_str, user_email))
                    cursor.execute("INSERT INTO daily_price_snapshot VALUES (?, ?, ?, ?)", (row['اسم السلعة'], row['سعر البيع ج.م'], today_str, user_email))
                    conn.commit()
                    st.toast(f"✅ تم حفظ التعديلات لـ {row['اسم السلعة']} وتعميمها!")
                    st.rerun()

            with st.expander("🗑️ قسم حذف السلع"):
                del_id = st.selectbox("اختر السلعة للحذف النهائي", prod_data['id'].tolist(), format_func=lambda x: prod_data[prod_data['id'] == x]['اسم السلعة'].values)
                if st.button("تأكيد الحذف"):
                    cursor.execute("DELETE FROM products WHERE id = ? AND user_email = ?", (del_id, user_email))
                    conn.commit()
                    st.rerun()
        else:
            st.info("المخزن فارغ تماماً.")

    # --- 👥 التبويب الثاني: سجل الموردين والعملاء ---
    with tab2:
        st.subheader("🏭 سجل الموردين (الدائنين)")
        with st.expander("➕ إضافة مورد جديد للدفتر"):
            s_name = st.text_input("اسم المورد الجديد")
            s_bal = st.number_input("حساب المورد الابتدائي (ج.م)", value=None, placeholder="الحساب الافتتاحي المستحق له...")
            if st.button("حفظ المورد"):
                if s_name:
                    final_bal = s_bal if s_bal is not None else 0.0
                    cursor.execute("INSERT INTO suppliers (name, balance, user_email) VALUES (?, ?, ?)", (s_name, final_bal, user_email))
                    conn.commit()
                    st.rerun()
        try:
            supp_df = pd.read_sql_query("SELECT id, name, balance FROM suppliers WHERE user_email = ?", conn)
            if not supp_df.empty:
                supp_df.columns = ['كود المورد', 'اسم المورد', 'الحساب المستحق له ج.م']
        except:
            supp_df = pd.DataFrame()
        st.dataframe(supp_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("👥 سجل العملاء (المدينين)")
        with st.expander("➕ إضافة عميل جديد للدفتر"):
            c_name = st.text_input("اسم العميل الجديد")
            c_bal = st.number_input("حساب العميل الابتدائي (ج.م)", value=None, placeholder="مديونية العميل الحالية...")
            if st.button("حفظ العميل"):
                if c_name:
                    final_c_bal = c_bal if c_bal is not None else 0.0
                    cursor.execute("INSERT INTO customers (name, balance, user_email) VALUES (?, ?, ?)", (c_name, final_c_bal, user_email))
                    conn.commit()
                    st.rerun()
        try:
            cust_df = pd.read_sql_query("SELECT id, name, balance FROM customers WHERE user_email = ?", conn)
            if not cust_df.empty:
