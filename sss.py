import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي
st.set_page_config(page_title="سيستم محل الجملة المتطور", layout="centered")

# الاتصال بقاعدة البيانات السحابية المشتركة
conn = sqlite3.connect('gomla_advanced_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول المتطورة (مرتبطة بالإيميل المشترك)
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    (id INTEGER PRIMARY KEY, name TEXT, type TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS price_history 
    (product_name TEXT, old_price REAL, new_price REAL, date TEXT, user_email TEXT)''')

conn.commit()

# --- إدارة جلسة تسجيل الدخول (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 1. شاشة تسجيل الدخول بالحساب المشترك ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #1E88E5;'>🔐 تسجيل دخول النظام المشترك</h2>", unsafe_allow_html=True)
    st.write("أدخل البريد الإلكتروني الموحد لربط هذا الهاتف بباقي هواتف المحل.")
    
    email_input = st.text_input("البريد الإلكتروني المشترك (Email)", value="").strip().lower()
    password_input = st.text_input("كلمة المرور (Password)", type="password")
    
    if st.button("دخول ومزامنة الأجهزة", use_container_width=True):
        if email_input and password_input:
            st.session_state.logged_in = True
            st.session_state.user_email = email_input
            
            # إضافة سلع تجريبية لهذا الحساب الجديد إذا كان فارغاً
            cursor.execute("SELECT count(*) FROM products WHERE user_email = ?", (email_input,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock, user_email) VALUES (?, ?, ?, ?, ?)", 
                               ('طن دقيق الهدى', 14000, 15000, 50, email_input))
                cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock, user_email) VALUES (?, ?, ?, ?, ?)", 
                               ('كرتونة زيت سلايت', 650, 700, 100, email_input))
                conn.commit()
            st.rerun()
        else:
            st.error("برجاء إدخال البريد الإلكتروني وكلمة المرور بشكل صحيح")

# --- 2. لوحة التحكم الرئيسية بعد تسجيل الدخول ---
else:
    user_email = st.session_state.user_email
    
    # ترويسة التطبيق تظهر الحساب النشط وزر خروج
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        st.markdown(f"🟢 **متصل ومزامن:** `{user_email}`")
    with col_logout:
        if st.button("خروج"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
            
    st.markdown("<hr style='margin-top:0; margin-bottom:15px;'>", unsafe_allow_html=True)

    # التبويبات الرئيسية للنظام
    tab1, tab2, tab3 = st.tabs(["📊 أسعار اليوم", "👥 الديون والحسابات", "📅 مرجعيات وأرشيف الأسعار"])

    # --- التبويب الأول: تحديث الأسعار اليومية ---
    with tab1:
        st.subheader("تحديث أسعار السلع لحظياً")
        
        # جلب المنتجات الخاصة بهذا الحساب فقط
        products_df = pd.read_sql_query("SELECT * FROM products WHERE user_email = ?", conn, params=(user_email,))
        
        for index, row in products_df.iterrows():
            st.markdown(f"📦 **{row['name']}**")
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"(سعر الشراء الحالي: {row['purchase_price']} ج.م | كمية المخزن: {row['stock']})")
            with c2:
                new_price = st.number_input(f"سعر اليوم (البيع)", value=float(row['today_price']), key=f"p_{row['id']}")
                
            # إذا قام المستخدم بتعديل السعر
            if new_price != row['today_price']:
                cursor.execute("UPDATE products SET today_price = ? WHERE id = ? AND user_email = ?", (new_price, row['id'], user_email))
                # حفظ في المرجعيات والأرشيف اليومي
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute("INSERT INTO price_history VALUES (?, ?, ?, ?, ?)", 
                               (row['name'], row['today_price'], new_price, current_date, user_email))
                conn.commit()
                st.toast(f"✅ تم تحديث السعر وتعميمه على باقي الهواتف!")
                st.rerun()

    # --- التبويب الثاني: الديون والحسابات ---
    with tab2:
        st.subheader("دفتر ديون العملاء والموردين الآجل")
        
        with st.expander("➕ إضافة اسم جديد للدفتر"):
            name = st.text_input("اسم الشخص أو المحل")
            acc_type = st.selectbox("نوع الحساب", ["عميل (مدين - عليه فلوس)", "مورد (دائن - يطلب فلوس)"])
            balance = st.number_input("إجمالي الحساب الحالي (ج.م)", value=0.0)
            if st.button("حفظ في الدفتر المشترك"):
                if name:
                    cursor.execute("INSERT INTO accounts (name, type, balance, user_email) VALUES (?, ?, ?, ?)", 
                                   (name, acc_type, balance, user_email))
                    conn.commit()
                    st.success(f"تم تسجيل {name} وتحديث الدفتر المشترك!")
                    st.rerun()

        st.markdown("### 📋 كشف الحسابات المشترك حالياً")
        accounts_df = pd.read_sql_query("SELECT name as 'الاسم', type as 'النوع', balance as 'الحساب (ج.م)' FROM accounts WHERE user_email = ?", conn, params=(user_email,))
        st.dataframe(accounts_df, use_container_width=True)

    # --- 3. التبويب الثالث: مرجعيات وأرشيف الأسعار باليوم ---
    with tab3:
        st.subheader("📅 مرجعيات حركة الأسعار اليومية")
        st.write("اختر أو ابحث عن التاريخ لمراجعة أسعار السلع في الأيام السابقة.")
        
        # جلب تواريخ الأرشيف المتوفرة لهذا الحساب لتسهيل الاختيار
        history_dates_df = pd.read_sql_query("SELECT DISTINCT SUBSTR(date, 1, 10) as short_date FROM price_history WHERE user_email = ? ORDER BY date DESC", conn, params=(user_email,))
        
        if not history_dates_df.empty:
            search_date = st.selectbox("اختر تاريخ اليوم المراد مراجعته", history_dates_df['short_date'].tolist())
            
            st.markdown(f"📊 **جدول مرجعيات الأسعار ليوم: {search_date}**")
            # جلب سجلات هذا اليوم بالتحديد
            day_history_df = pd.read_sql_query(
                "SELECT product_name as 'السلعة', old_price as 'السعر القديم', new_price as 'السعر الجديد', date as 'الوقت الفعلي للتحديث' FROM price_history WHERE user_email = ? AND date LIKE ?", 
                conn, params=(user_email, f"{search_date}%")
            )
            st.dataframe(day_history_df, use_container_width=True)
        else:
            st.info("💡 لا توجد مرجعيات مسجلة بعد. الأرشيف سيحفظ تلقائياً هنا بمجرد قيامك بتعديل أسعار السلع من شاشة أسعار اليوم.")
