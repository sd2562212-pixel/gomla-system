import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد واجهة النظام السحابي الحديثة جداً
st.set_page_config(page_title="سيستم محل الجملة الذكي - الإصدار الحديث", layout="centered")

# تحسين مظهر الخلفيات والأزرار عبر تصفيف مخصص
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B; border-radius: 8px; padding: 10px 20px; color: #94A3B8; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #3B82F6 !important; color: white !important; }
    .main-card {
        background-color: #0F172A; padding: 20px; border-radius: 12px; 
        border-left: 5px solid #3B82F6; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# الاتصال بقاعدة بيانات جديدة ونظيفة ومستقرة تماماً
conn = sqlite3.connect('gomla_modern_v11_system.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول المحاسبية المتطورة
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
    st.markdown("<h1 style='text-align: center; color: #3B82F6; margin-bottom:20px;'>🏬 سيستم الجملة الذكي</h1>", unsafe_allow_html=True)
    auth_mode = st.radio("اختر العملية المراد القيام بها:", ["🔑 تسجيل دخول بحساب سابق", "➕ إنشاء حساب جديد للمحل"], horizontal=True)
    st.markdown("<hr style='margin:15px 0; border-color: #334155;'>", unsafe_allow_html=True)

    if auth_mode == "➕ إنشاء حساب جديد للمحل":
        st.markdown("<h3 style='text-align: center; color: #10B981;'>📝 تسجيل المحل لأول مرة</h3>", unsafe_allow_html=True)
        new_email = st.text_input("البريد الإلكتروني الجديد (Email)", key="reg_email").strip().lower()
        new_password = st.text_input("اختر كلمة المرور (Password)", type="password", key="reg_pass")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="reg_confirm")
        
        if st.button("🚀 إنشاء حسابك السحابي وتفعيل الأجهزة", use_container_width=True):
            if new_email and new_password:
                if new_password == confirm_password:
                    try:
                        cursor.execute("INSERT INTO users VALUES (?, ?)", (new_email, new_password))
                        conn.commit()
                        st.success("🎉 تم إنشاء الحساب بنجاح! انتقل الآن لتبويب 'تسجيل دخول' لفتح لوحة التحكم.")
                    except sqlite3.IntegrityError:
                        st.error("⚠️ هذا البريد الإلكتروني مسجل بالفعل بالنظام من قبل!")
                else:
                    st.error("❌ كلمات المرور غير متطابقة")
            else:
                st.error("برجاء ملء جميع الخانات")

    elif auth_mode == "🔑 تسجيل دخول بحساب سابق":
        st.markdown("<h3 style='text-align: center; color: #3B82F6;'>🔐 تسجيل دخول النظام المشترك</h3>", unsafe_allow_html=True)
        email_input = st.text_input("البريد الإلكتروني (Email)", key="log_email").strip().lower()
        password_input = st.text_input("كلمة المرور (Password)", type="password", key="log_pass")
        
        if st.button("⚡ دخول ومزامنة كافة الهواتف", use_container_width=True):
            if email_input and password_input:
                cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email_input, password_input))
                if cursor.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ البيانات غير صحيحة! تأكد من حسابك أو قم بإنشاء حساب جديد للمحل.")
            else:
                st.error("برجاء إدخال البيانات المطلوبة")

# --- 2. لوحة التحكم الرئيسية الحديثة جداً ---
else:
    user_email = st.session_state.user_email
    
    # ترويسة علوية عصرية
    col_user, col_logout = st.columns([3, 1])
    with col_user:
        st.markdown(f"🌟 **السيستم نشط ومزامن:** `{user_email}`")
    with col_logout:
        if st.button("🔒 خروج آمن", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
            
    st.markdown("<hr style='margin-top:0; margin-bottom:20px; border-color: #334155;'>", unsafe_allow_html=True)

    # جلب إحصائيات سريعة للمؤشرات الذكية
    cursor.execute("SELECT COUNT(*) FROM products WHERE user_email=?", (user_email,))
    total_p = cursor.fetchone()[0]
    cursor.execute("SELECT IFNULL(SUM(balance), 0) FROM customers WHERE user_email=?", (user_email,))
    total_c_deb = cursor.fetchone()[0]
    
    # عرض مؤشرات الأداء العصرية في بطاقات رقمية ملونة
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="📦 إجمالي أصناف المخزن", value=f"{total_p} صنف")
    with m2:
        st.metric(label="💸 ديون السوق (مستحقات العملاء)", value=f"{total_c_deb:,.1f} ج.م", delta="حسابات العملاء")

    st.markdown("<br>", unsafe_allow_html=True)

    # التبويبات والمجلدات الحسابية المفصلة والجديدة للسيستم بتصميم مسطح
    tab1, tab2, tab3, tab4 = st.tabs(["📦 إدارة السلع والمخزن", "👥 الموردين والعملاء", "🧾 تسجيل الفواتير الذكي", "📅 المرجعيات والأرشيف التاريخي"])

    # --- التبويب الأول: إدارة المخزن والأسعار الحالية ---
    with tab1:
        st.markdown("<h4 style='color:#3B82F6;'>🏢 مستودع البضائع والأسعار الحالية</h4>", unsafe_allow_html=True)
        
        with st.expander("➕ إضافة سلعة جديدة للمخزن"):
            p_name = st.text_input("اسم السلعة الجديد (مثال: طن أرز المروة)")
            p_today = st.number_input("سعر البيع الحالي (ج.م)", value=None, placeholder="اكتب سعر البيع المباشر...")
            p_stock = st.number_input("الالكمية المتاحة حالياً بالمخزن", value=None, placeholder="اكتب كمية المخزن الأولية...", step=1)
            
            if st.button("✨ حفظ وتثبيت السلعة بالمخزن"):
                if p_name and p_today is not None and p_stock is not None:
                    cursor.execute("INSERT INTO products (name, today_price, stock, user_email) VALUES (?, ?, ?, ?)", (p_name, p_today, p_stock, user_email))
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO daily_price_snapshot VALUES (?, ?, ?, ?)", (p_name, p_today, today_str, user_email))
                    conn.commit()
                    st.success(f"✅ تم تسجيل {p_name} بالمخزن وتثبيت سعرها السحابي!")
                    st.rerun()
                else:
                    st.error("❌ برجاء ملء كافة الخانات أولاً!")
                    
        st.markdown("---")
        st.subheader("📋 قائمة جرد المخزن وتحديث الأسعار التفاعلية")
        st.caption("💡 لتعديل سعر منتج بشكل دائم، اكتب السعر الجديد في خانته بجدول الإكسيل التفاعلي أدناه واضغط Go/تم بالآيفون.")
        
        prod_data = pd.read_sql_query("SELECT id, name, today_price, stock FROM products WHERE user_email = ?", conn)
        
        if not prod_data.empty:
            prod_data.columns = ['الكود', 'اسم السلعة 📦', 'سعر البيع ج.م 💰', 'الكمية المتاحة 🧮']
            edited_df = st.data_editor(prod_data, hide_index=True, use_container_width=True, disabled=["الكود", "اسم السلعة 📦"])
            
            for idx, row in edited_df.iterrows():
                old_row = prod_data.iloc[idx]
                if row['سعر البيع ج.م 💰'] != old_row['سعر البيع ج.م 💰'] or row['الكمية المتاحة 🧮'] != old_row['الكمية المتاحة 🧮']:
                    cursor.execute("UPDATE products SET today_price = ?, stock = ? WHERE id = ? AND user_email = ?", (row['سعر البيع ج.م 💰'], row['الكمية المتاحة 🧮'], row['الكود'], user_email))
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("DELETE FROM daily_price_snapshot WHERE product_name = ? AND snapshot_date = ? AND user_email = ?", (row['اسم السلعة 📦'], today_str, user_email))
                    cursor.execute("INSERT INTO daily_price_snapshot VALUES (?, ?, ?, ?)", (row['اسم السلعة 📦'], row['سعر البيع ج.م 💰'], today_str, user_email))
                    conn.commit()
                    st.toast(f"✅ تم تعميم وحفظ تعديلات {row['اسم السلعة 📦']}!")
                    st.rerun()

            with st.expander("🗑️ قسم حذف السلع السريع"):
                del_id = st.selectbox("اختر السلعة للحذف النهائي", prod_data['الكود'].tolist(), format_func=lambda x: prod_data[prod_data['الكود'] == x]['اسم السلعة 📦'].values[0])
                if st.button("🗑️ تأكيد حذف السلعة المحددة"):
                    cursor.execute("DELETE FROM products WHERE id = ? AND user_email = ?", (del_id, user_email))
                    conn.commit()
                    st.rerun()
        else:
            st.info("المخزن فارغ تماماً حالياً.")

