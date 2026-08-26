import flet as ft
import sqlite3
from datetime import datetime

# --- 1. إعداد قاعدة البيانات وتحديث الجداول لتستوعب كافة الميزات الجديدة ---
local_conn = sqlite3.connect("local_gomla.db", check_same_thread=False)
local_cursor = local_conn.cursor()

# تفعيل نظام المفاتيح الأجنبية لربط الجداول
local_cursor.execute("PRAGMA foreign_keys = ON;")

# إنشاء جدول الحسابات/المستخدمين للفتح من كذا تليفون
local_cursor.execute('''CREATE TABLE IF NOT EXISTS users 
    (email TEXT PRIMARY KEY, password TEXT, store_name TEXT)''')

# جدول المنتجات
local_cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id TEXT PRIMARY KEY, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER, last_updated TEXT)''')

# جدول سجل الأسعار التاريخي (يحفظ تغير الأسعار كل يوم للمرجعية)
local_cursor.execute('''CREATE TABLE IF NOT EXISTS price_history 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, price REAL, updated_at TEXT)''')

# جدول الحسابات المحاسبية (العملاء والموردين) مع تحديد نوع الحساب والماليات
local_cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, phone TEXT, balance REAL)''') # type: 'عميل' أو 'مورد' | balance: موجب (لنا) / سالب (علينا)

# جدول الفواتير التاريخي (شراء وبيع) مع التاريخ الشهرى واليومي
local_cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, account_name TEXT, total REAL, date TEXT, month TEXT)''') # type: 'شراء' أو 'بيع' | month: '2026-08'

local_conn.commit()


def main(page: ft.Page):
    page.title = "سيستم محل الجملة الاحترافي"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 20
    
    # متغيرات الجلسة النشطة
    current_user = ft.Ref[ft.Text]()
    active_email = ""

    # دالة لتحديث الشاشة بالكامل بعد أي حركة محاسبية
    def refresh_all_views():
        page.clean()
        show_main_dashboard()

    # --- شاشة تسجيل الدخول وإنشاء حساب أول مرة ---
    def show_auth_screen():
        page.clean()
        
        email_input = ft.TextField(label="البريد الإلكتروني", keyboard_type=ft.KeyboardType.EMAIL)
        pass_input = ft.TextField(label="كلمة المرور", password=True, can_reveal_password=True)
        store_input = ft.TextField(label="اسم المحل (عند التسجيل لأول مرة)")
        
        def login_logic(e):
            nonlocal active_email
            email = email_input.value.strip().lower()
            password = pass_input.value
            
            if not email or not password:
                page.snack_bar = ft.SnackBar(ft.Text("❌ برجاء ملء الحقول الأساسية"))
                page.snack_bar.open = True
                page.update()
                return
            
            # التحقق إذا كان الحساب موجوداً ومسجلاً من قبل لتسجيل الدخول من أي هاتف
            local_cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            user = local_cursor.fetchone()
            
            if user:
                active_email = email
                show_main_dashboard()
            else:
                # إذا لم يكن موجوداً، يتم تسجيله تلقائياً كحساب جديد لأول مرة
                store = store_input.value.strip() if store_input.value else "محل الجملة"
                try:
                    local_cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (email, password, store))
                    local_conn.commit()
                    active_email = email
                    page.snack_bar = ft.SnackBar(ft.Text("🎉 تم إنشاء حسابك الجديد بنجاح والمزامنة جاهزة!"))
                    page.snack_bar.open = True
                    show_main_dashboard()
                except sqlite3.IntegrityError:
                    page.snack_bar = ft.SnackBar(ft.Text("❌ كلمة المرور غير صحيحة لهذا الحساب"))
                    page.snack_bar.open = True
                    page.update()

        auth_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("🔐 نظام إدارة الجملة المشترك", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("سجل دخولك أو أنشئ حساباً لأول مرة للاستخدام على عدة هواتف تزامناً", color=ft.Colors.GREY_400, size=12),
                    ft.Divider(),
                    email_input,
                    pass_input,
                    store_input,
                    ft.ElevatedButton("دخول / تفعيل الحساب ومزامنة الأجهزة", on_click=login_logic, bgcolor=ft.Colors.BLUE_ACCENT, color=ft.Colors.WHITE, width=400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30
            )
        )
        page.add(ft.Row([auth_card], alignment=ft.MainAxisAlignment.CENTER))
        page.update()

    # --- لوحة التحكم الرئيسية بعد تخطي بوابة الأمان ---
    def show_main_dashboard():
        page.clean()
        
        # الترويسة العلوية للحساب النشط والخروج
        header = ft.Container(
            content=ft.Row([
                ft.Text(f"🟢 متصل ومزامن: {active_email}", color=ft.Colors.GREEN_ACCENT, weight=ft.FontWeight.W_500),
                ft.ElevatedButton("خروج", on_click=lambda e: show_auth_screen(), bgcolor=ft.Colors.RED_800, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.SURFACE_CONTAINER, padding=12, border_radius=8
        )
        page.add(header)

        # ----------------------------------------------------
        # تبويب 1: قائمة المنتجات والأسعار والتحديث (مع حذف السلع تلقائياً)
        # ----------------------------------------------------
        def get_products_view():
            prod_container = ft.Column()
            
            # نموذج إضافة منتج جديد
            p_id = ft.TextField(label="كود السلعة", width=100)
            p_name = ft.TextField(label="اسم السلعة", expand=True)
            p_purch = ft.TextField(label="سعر الشراء", width=100)
            p_sell = ft.TextField(label="سعر البيع الحالي", width=120)
            p_stock = ft.TextField(label="الكمية بالمخزن", width=100)
            
            def add_product_click(e):
                if p_id.value and p_name.value:
                    local_cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?, ?)",
                                         (p_id.value, p_name.value, float(p_purch.value or 0), float(p_sell.value or 0), int(p_stock.value or 0), datetime.now().strftime("%Y-%m-%d")))
                    # حفظ السعر في السجل التاريخي أيضاً للمرجعية
                    local_cursor.execute("INSERT INTO price_history (product_id, price, updated_at) VALUES (?, ?, ?)",
                                         (p_id.value, float(p_sell.value or 0), datetime.now().strftime("%Y-%m-%d %H:%M")))
                    local_conn.commit()
                    refresh_all_views()
            
            add_row = ft.Row([p_id, p_name, p_purch, p_sell, p_stock, ft.IconButton(ft.Icons.ADD_BOX, on_click=add_product_click, icon_color=ft.Colors.GREEN_ACCENT)])
            
            # عرض قائمة المنتجات مع ميزة الإزالة التلقائية من السيستم وزر تعديل السعر السريع
            product_list = ft.Column()
            local_cursor.execute("SELECT * FROM products")
            for row in local_cursor.fetchall():
                pid, name, purch, sell, stock, _ = row
                
                def make_update_price(p_id_target):
                    return lambda e: update_price_direct(p_id_target, e.control.value)
                
                def make_delete_prod(p_id_target):
                    return lambda e: delete_product_direct(p_id_target)

                price_field = ft.TextField(value=str(sell), width=100, on_submit=make_update_price(pid))
                
                product_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"📦 {name} (كود: {pid})", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"شراء: {purch} ج.م | المخزن الحالي: {stock}", size=12, color=ft.Colors.GREY_400)
                                ], expand=True),
                                ft.Row([
                                    ft.Text("سعر اليوم:"),
                                    price_field,
                                    ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_ACCENT, on_click=make_delete_prod(pid), tooltip="إزالة السلعة تلقائياً من التطبيق")
                                ])
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=12
                        )
                    )
                )
            
            prod_container.controls.extend([
                ft.Text("➕ إضافة منتج جديد للمخزن:", size=16, weight=ft.FontWeight.BOLD),
                add_row,
                ft.Divider(),
                ft.Text("📊 قائمة المنتجات والأسعار اللحظية:", size=16, weight=ft.FontWeight.BOLD),
                product_list
            ])
            return prod_container

        def update_price_direct(pid, val):
            try:
                new_p = float(val)
                local_cursor.execute("UPDATE products SET today_price=? WHERE id=?", (new_p, pid))
                local_cursor.execute("INSERT INTO price_history (product_id, price, updated_at) VALUES (?, ?, ?)", (pid, new_p, datetime.now().strftime("%Y-%m-%d %H:%M")))
                local_conn.commit()
                refresh_all_views()
            except: pass

        def delete_product_direct(pid):
            local_cursor.execute("DELETE FROM products WHERE id=?", (pid,))
            local_conn.commit()
            refresh_all_views()

        # ----------------------------------------------------
        # تبويب 2: سجل تاريخ الأسعار (مرجعية الأيام السابقة)
        # ----------------------------------------------------
        def get_history_view():
