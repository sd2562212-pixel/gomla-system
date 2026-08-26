import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي
st.set_page_config(page_title="سيستم محل الجملة الاحترافي", layout="centered")

# الاتصال بقاعدة البيانات السحابية المشتركة
conn = sqlite3.connect('gomla_advanced_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول (إضافة جدول المستخدمين الجدد)
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
    (email TEXT PRIMARY KEY, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER, user_email TEXT)''')
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

# --- 1. شاشات الحسابات الموحدة ---
if not st.session_state.logged_in:
    # اختيار وضع الشاشة (تسجيل دخول أو إنشاء حساب)
    auth_mode = st.radio("اختر العملية المراد القيام بها:", ["🔑 تسجيل دخول بحساب سابق", "➕ إنشاء حساب جديد للمحل"], horizontal=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    if auth_mode == "➕ إنشاء حساب جديد للمحل":
        st.markdown("<h3 style='text-align: center; color: #4CAF50;'>📝 إنشاء حساب جديد للمحل</h3>", unsafe_allow_html=True)
        st.write("استخدم هذا القسم لإنشاء حساب المحل لأول مرة فقط، ثم وزع الإيميل والباسورد على الموظفين.")
        
        new_email = st.text_input("البريد الإلكتروني الجديد (Email)", key="reg_email").strip().lower()
        new_password = st.text_input("اختر كلمة المرور (Password)", type="password", key="reg_pass")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="reg_confirm")
        
        if st.button("تأجيل وإنشاء الحساب الحركي", use_container_width=True):
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
        st.write("أدخل البريد الإلكتروني الذي قمت بإنشائه سابقاً لربط هذا الهاتف بالمخزن.")
        
        email_input = st.text_input("البريد الإلكتروني (Email)", key="log_email").strip().lower()
        password_input = st.text_input("كلمة المرور (Password)", type="password", key="log_pass")
        
        if st.button("دخول ومزامنة الأجهزة", use_container_width=True):
            if email_input and password_input:
                # التحقق من وجود الحساب في قاعدة البيانات
                cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email_input, password_input))
                user_record = cursor.fetchone()
                
                if user_record:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة! تأكد من كتابتهم بدقة أو قم بإنشاء حساب جديد.")
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

    tab1, tab2, tab3 = st.tabs(["📊 أسعار اليوم والمخزن", "👥 الديون والحسابات", "📅 مرجعيات وأرشيف الأسعار"])

    # --- التبويب الأول: إدارة المخزن وتحديث الأسعار ---
    with tab1:
        st.subheader("إدارة مخزن وبضاعة المحل")
        
        with st.expander("➕ إضافة بضاعة/سلعة جديدة للمخزن"):
            new_p_name = st.text_input("اسم السلعة (مثال: طن أرز الفيروز)")
            new_p_purchase = st.number_input("سعر الشراء الحالي (ج.م)", value=0.0)
            new_p_today = st.number_input("سعر البيع الافتتاحي لليوم (ج.م)", value=0.0)
            new_p_stock = st.number_input("الكمية المتوفرة بالمخزن", value=0, step=1)
            
            if st.button("حفظ السلعة بالمخزن المشترك"):
                if new_p_name:
                    cursor.execute("INSERT INTO products (name, purchase_price, today_price, stock, user_email) VALUES (?, ?, ?, ?, ?)", 
                                   (new_p_name, new_p_purchase, new_p_today, new_p_stock, user_email))
                    conn.commit()
                    st.success(f"تمت إضافة {new_p_name} للمخزن بنجاح!")
                    st.rerun()
        
        st.markdown("---")
        st.subheader("🔄 تحديث أسعار السلع لحظياً")
        
        products_df = pd.read_sql_query("SELECT * FROM products WHERE user_email = ?", conn, params=(user_email,))
        
        if products_df.empty:
            st.info("💡 المخزن فارغ حالياً. قم بالضغط على الزر بالأعلى لإضافة أول سلعة لمحلك بيدك.")
        else:
            for index, row in products_df.iterrows():
                st.markdown(f"📦 **{row['name']}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"(الشراء: {row['purchase_price']} | المخزن: {row['stock']})")
                with c2:
                    new_price = st.number_input(f"سعر اليوم", value=float(row['today_price']), key=f"p_{row['id']}")
                with c3:
                    if st.button("🗑️ حذف", key=f"del_{row['id']}"):
                        cursor.execute("DELETE FROM products WHERE id = ? AND user_email = ?", (row['id'], user_email))
                        conn.commit()
                        st.toast(f"❌ تم حذف {row['name']}")
                        st.rerun()
                    
                if new_price != row['today_price']:
                    cursor.execute("UPDATE products SET today_price = ? WHERE id = ? AND user_email = ?", (new_price, row['id'], user_email))
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cursor.execute("INSERT INTO price_history VALUES (?, ?, ?, ?, ?)", 
                                   (row['name'], row['today_price'], new_price, current_date, user_email))
                    conn.commit()
                    st.toast(f"✅ تم تحديث السعر وتعميمه!")
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
        
        history_dates_df = pd.read_sql_query("SELECT DISTINCT SUBSTR(date, 1, 10) as short_date FROM price_history WHERE user_email = ? ORDER BY date DESC", conn, params=(user_email,))
        
        if not history_dates_df.empty:
            search_date = st.selectbox("اختر تاريخ اليوم المراد مراجعته", history_dates_df['short_date'].tolist())
            st.markdown(f"📊 **جدول مرجعيات الأسعار ليوم: {search_date}**")
            day_history_df = pd.read_sql_query(
                "SELECT product_name as 'السلعة', old_price as 'السعر القديم', new_price as 'السعر الجديد', date as 'الوقت الفعلي للتحديث' FROM price_history WHERE user_email = ? AND date LIKE ?", 
                conn, params=(user_email, f"{search_date}%")
            )
            st.dataframe(day_history_df, use_container_width=True)
        else:
            st.info("💡 لا توجد مرجعيات مسجلة بعد. الأرشيف سيحفظ تلقائياً هنا بمجرد قيامك بتعديل أسعار السلع.")
