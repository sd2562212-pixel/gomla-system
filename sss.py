import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي
st.set_page_config(page_title="سيستم محل الجملة الذكي - إكسيل ستايل", layout="centered")

# الاتصال بقاعدة البيانات السحابية المشتركة
conn = sqlite3.connect('gomla_ultimate_excel_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول المحاسبية المتطورة
cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, today_price REAL, stock INTEGER, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS customers 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, balance REAL, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS price_history 
    (product_name TEXT, old_price REAL, new_price REAL, date TEXT, user_email TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_type TEXT, party_name TEXT, total_amount REAL, date TEXT, user_email TEXT)''')

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

    # التبويبات والمجلدات الحسابية المفصلة
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 أسعار البيع اليومية", "📦 إدارة المخزن", "👥 الموردين والعملاء", "🧾 تسجيل الفواتير", "📅 أرشيف السجلات والتاريخ"])

    # --- التبويب الأول: قائمة تعديل الأسعار اليومية فقط لليوم الحالي ---
    with tab1:
        st.subheader("🔄 تعديل أسعار البيع اليومية لحظياً")
        products_df = pd.read_sql_query("SELECT * FROM products WHERE user_email = ?", conn, params=(user_email,))
        
        if products_df.empty:
            st.info("💡 المخزن فارغ. أضف بعض المنتجات من تبويب 'إدارة المخزن' لتتحكم في أسعار اليوم هنا.")
        else:
            st.caption("💡 بعد كتابة السعر، اضغط على زر 'Go' أو 'تم' (Done) في كيبورد الآيفون لحفظ السعر وتعميمه فوراً.")
            for index, row in products_df.iterrows():
                st.markdown(f"📦 **{row['name']}**")
                c_info, c_input = st.columns(2)
                with c_info:
                    st.write(f"(المخزن الحالي: {row['stock']})")
                with c_input:
                    new_price = st.number_input(f"سعر البيع لليوم", value=None, placeholder="اكتب السعر وضغط Go...", key=f"sale_p_{row['id']}")
                    
                if new_price is not None and new_price != row['today_price']:
                    cursor.execute("UPDATE products SET today_price = ? WHERE id = ? AND user_email = ?", (new_price, row['id'], user_email))
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cursor.execute("INSERT INTO price_history VALUES (?, ?, ?, ?, ?)", (row['name'], row['today_price'], new_price, current_time, user_email))
                    conn.commit()
                    st.toast(f"✅ تم تعميم سعر اليوم لـ {row['name']}!")
                    st.rerun()

    # --- التبويب الثاني: إدارة المخزن الأساسي وإضافة وحذف البضائع ---
    with tab2:
        st.subheader("📦 إدارة أصل البضائع والمخزن")
        with st.expander("➕ إضافة بضاعة/سلعة جديدة للمخزن الأصلي"):
            p_name = st.text_input("اسم السلعة")
            # تم حذف خانة سعر الشراء تماماً من هنا
            p_today = st.number_input("سعر البيع الابتدائي (ج.م)", value=None, placeholder="اكتب سعر البيع الافتتاحي...")
            p_stock = st.number_input("الكمية المتاحة بالمخزن", value=None, placeholder="اكتب الكمية المتاحة حالياً...", step=1)
            
            if st.button("حفظ السلعة بالمخزن الأصلي"):
                if p_name and p_today is not None and p_stock is not None:
                    cursor.execute("INSERT INTO products (name, today_price, stock, user_email) VALUES (?, ?, ?, ?)", (p_name, p_today, p_stock, user_email))
                    conn.commit()
                    st.success(f"تم تسجيل {p_name} بالمخزن بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ برجاء ملء كافة الخانات وتحديد البيانات أولاً!")
                    
        st.markdown("---")
        st.subheader("📋 قائمة إكسيل المنظمة لجرد المخزن")
        prod_df = pd.read_sql_query("SELECT id as 'كود السلعة', name as 'اسم السلعة', today_price as 'سعر بيع اليوم ج.م', stock as 'الكمية المتاحة' FROM products WHERE user_email = ?", conn, params=(user_email,))
        if not prod_df.empty:
            st.dataframe(prod_df, use_container_width=True, hide_index=True)
            
            with st.expander("🗑️ قسم حذف السلع من المخزن"):
                del_id = st.selectbox("اختر السلعة المراد حذفها نهائياً", prod_df['كود السلعة'].tolist())
                if st.button("تأكيد حذف السلعة المختارة"):
                    cursor.execute("DELETE FROM products WHERE id = ? AND user_email = ?", (del_id, user_email))
                    conn.commit()
                    st.rerun()
        else:
            st.info("المخزن فارغ تماماً.")

    # --- التبويب الثالث: سجل الموردين والعملاء على شكل إكسيل ---
    with tab3:
        st.subheader("🏭 سجل الموردين (الدائنين)")
        with st.expander("➕ إضافة مورد جديد للدفتر"):
            s_name = st.text_input("اسم المورد الجديد")
            s_bal = st.number_input("حساب المورد الابتدائي (ج.م)", value=None, placeholder="اكتب الحساب المالي الافتتاحي...")
            if st.button("حفظ المورد"):
                if s_name:
                    final_bal = s_bal if s_bal is not None else 0.0
                    cursor.execute("INSERT INTO suppliers (name, balance, user_email) VALUES (?, ?, ?)", (s_name, final_bal, user_email))
                    conn.commit()
                    st.rerun()
        supp_df = pd.read_sql_query("SELECT id as 'كود المورد', name as 'اسم المورد', balance as 'الحساب المالي المستحق له ج.م' FROM suppliers WHERE user_email = ?", conn, params=(user_email,))
        st.dataframe(supp_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("👥 سجل العملاء (المدينين)")
        with st.expander("➕ إضافة عميل جديد للدفتر"):
            c_name = st.text_input("اسم العميل الجديد")
            c_bal = st.number_input("حساب العميل المديونية الابتدائية (ج.م)", value=None, placeholder="اكتب مديونية العميل...")
            if st.button("حفظ العميل"):
                if c_name:
                    final_c_bal = c_bal if c_bal is not None else 0.0
                    cursor.execute("INSERT INTO customers (name, balance, user_email) VALUES (?, ?, ?)", (c_name, final_c_bal, user_email))
                    conn.commit()
                    st.rerun()
