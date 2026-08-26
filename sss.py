import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام البسيطة والواضحة
st.set_page_config(page_title="سيستم محل الجملة الشامل", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🚀 سيستم محل الجملة الشامل</h1>", unsafe_allow_html=True)

# الاتصال بقاعدة البيانات المحلية المشتركة تلقائياً (إصدار محدث ومستقر)
conn = sqlite3.connect('gomla_shop_v1_advanced_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول الأساسية المباشرة للنظام
cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, today_price REAL, stock INTEGER, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS price_history 
    (product_name TEXT, price REAL, date TEXT, month_str TEXT, user_email TEXT)''')

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
        
        if st.button("🚀 تفعيل وإنشاء الحساب", use_container_width=True):
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
        
        if st.button("⚡ دخول ومزامنة الأجهزة", use_container_width=True):
            if email_input and password_input:
                cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email_input, password_input))
                if cursor.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة!")
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

    # قائمة التنقل العلوية المريحة جداً للموبايل
    tab1, tab2, tab3, tab4 = st.tabs(["📊 أسعار اليوم", "👥 الديون والحسابات", "📦 المخزن والسلع الجديدة", "📅 جرد الأيام والشهور السابقة"])

    # --- التبويب الأول: شاشة تحديث الأسعار اليومية السريعة ---
    with tab1:
        st.subheader("تحديث أسعار السلع لحظياً")
        products = pd.read_sql_query("SELECT * FROM products WHERE user_email = ?", conn, params=(user_email,))
        
        if products.empty:
            st.info("💡 لا توجد سلع مضافة حالياً. اذهب لتبويب 'المخزن والسلع الجديدة' لإضافة أول صنف لمحلك.")
        else:
            st.caption("💡 اكتب السعر الجديد واضغط على زر Go أو تم (Done) في كيبورد الآيفون ليتم حفظ السعر وتعميمه فوراً.")
            for index, row in products.iterrows():
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"✨ **{row['name']}**\n\n(المخزن المتبقي: {row['stock']})")
                with col2:
                    # تعديل الخانات لتصبح فارغة تماماً بدون أصفار افتراضية
                    new_price = st.number_input(f"سعر البيع لليوم", value=None, placeholder="اكتب السعر هنا...", key=f"p_{row['id']}")
                    
                if new_price is not None and new_price != row['today_price']:
                    cursor.execute("UPDATE products SET today_price = ? WHERE id = ? AND user_email = ?", (new_price, row['id'], user_email))
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                    current_month = datetime.now().strftime("%Y-%m")
                    cursor.execute("INSERT INTO price_history VALUES (?, ?, ?, ?, ?)", (row['name'], new_price, current_time, current_month, user_email))
                    conn.commit()
                    st.toast(f"✅ تم تحديث سعر {row['name']} على جميع الهواتف!")
                    st.rerun()

# --- التبويب الثاني: شاشة الديون والحسابات (الداين والمدين) ---
with tab2:
    st.subheader("دفتر ديون العملاء والموردين الآجل")
    
    with st.expander("➕ إضافة عميل أو مورد جديد للدفتر"):
        name = st.text_input("اسم الشخص أو المحل")
        acc_type = st.selectbox("نوع الحساب", ["عميل (مدين - عليه فلوس)", "مورد (دائن - يطلب فلوس)"])
        # خانة فارغة للمديونية الابتدائية
        balance = st.number_input("الحساب الحالي الإجمالي (ج.م)", value=None, placeholder="اكتب الحساب المالي المبدئي...")
        if st.button("حفظ الحساب في الدفتر المشترك"):
            if name:
                final_bal = balance if balance is not None else 0.0
                cursor.execute("INSERT INTO accounts (name, type, balance, user_email) VALUES (?, ?, ?, ?)", (name, acc_type, final_bal, user_email))
                conn.commit()
                st.success(f"تم تسجيل {name} بنجاح!")
                st.rerun()

    st.markdown("### 📋 قائمة الحسابات المزامنة حالياً")
    accounts_df = pd.read_sql_query("SELECT name as 'الاسم', type as 'النوع', balance as 'الحساب الحالي (ج.م)' FROM accounts WHERE user_email = ?", conn, params=(user_email,))
    st.dataframe(accounts_df, use_container_width=True, hide_index=True)

# --- التبويب الثالث: شاشة إدارة المخزن والسلع الجديدة ---
with tab3:
    st.subheader("➕ إضافة صنف/بضاعة جديدة للمخزن")
    new_p_name = st.text_input("اسم السلعة (مثال: طن أرز الفيروز)")
    # خانات فارغة تماماً وسعر الشراء محذوف بالكامل بناءً على طلبك
    new_p_today = st.number_input("سعر البيع لليوم (ج.م)", value=None, placeholder="اكتب سعر بيع السلعة...")
    new_p_stock = st.number_input("الكمية المتوفرة بالمخزن", value=None, placeholder="اكتب كمية المخزن المتاحة...", step=1)
    
    if st.button("حفظ السلعة بالمخزن المشترك"):
        if new_p_name and new_p_today is not None and new_p_stock is not None:
            cursor.execute("INSERT INTO products (name, today_price, stock, user_email) VALUES (?, ?, ?, ?)", 
                           (new_p_name, new_p_today, new_p_stock, user_email))
            # حفظ لقطة سعرية أولية في سجل التواريخ
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            current_month = datetime.now().strftime("%Y-%m")
            cursor.execute("INSERT INTO price_history VALUES (?, ?, ?, ?, ?)", (new_p_name, new_p_today, current_time, current_month, user_email))
            conn.commit()
            st.success(f"تمت إضافة {new_p_name} للمخزن وتثبيتها بنجاح!")
            st.rerun()
        else:
            st.error("❌ برجاء ملء كافة الخانات وتحديد البيانات أولاً!")
            
    st.markdown("---")
    st.subheader("📦 حالة المخزن وجرد الكميات الحالي")
    products_df = pd.read_sql_query("SELECT name as 'السلعة 📦', today_price as 'سعر البيع النشط ج.م 💰', stock as 'الكمية المتبقية 🧮' FROM products WHERE user_email = ?", conn, params=(user_email,))
    st.dataframe(products_df, use_container_width=True, hide_index=True)

# --- التبويب الرابع: جداول أسعار الأيام السابقة والشهور والتواريخ (الأرشيف المتطور) ---
with tab4:
    st.subheader("📅 أرشيف وجرد السلع والتواريخ السابقة")
    search_mode = ft = st.radio("اختر طريقة جرد ومراجعة الأسعار السابقة:", ["🔍 جرد باليوم (التاريخ التفصيلي)", "📊 جرد بالشهور والأعوام"], horizontal=True)
    
    if search_mode == "🔍 جرد باليوم (التاريخ التفصيلي)":
        picked_date = st.date_input("اختر اليوم المراد مراجعة الأسعار فيه")
        date_str = picked_date.strftime("%Y-%m-%d")
        
        st.markdown(f"📋 **جدول الأسعار المسجلة في يوم {date_str}**")
        day_df = pd.read_sql_query(
            "SELECT product_name as 'اسم السلعة', price as 'سعر البيع المسجل ج.م', date as 'وقت التعديل الدقيق' FROM price_history WHERE user_email = ? AND date LIKE ?", 
