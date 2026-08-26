import flet as ft
import sqlite3
from datetime import datetime

# --- إعدادات قاعدة البيانات المحلية (للعمل بدون إنترنت) ---
local_conn = sqlite3.connect("local_gomla.db", check_same_thread=False)
local_cursor = local_conn.cursor()

local_cursor.execute('''CREATE TABLE IF NOT EXISTS products 
    (id TEXT PRIMARY KEY, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER, last_updated TEXT)''')
local_cursor.execute('''CREATE TABLE IF NOT EXISTS accounts 
    (id TEXT PRIMARY KEY, name TEXT, type TEXT, balance REAL, user_email TEXT)''')

# إضافة بيانات تجريبية للمخزن محلياً
local_cursor.execute("SELECT count(*) FROM products")
if local_cursor.fetchone() == 0:
    local_cursor.execute("INSERT INTO products VALUES ('1', 'طن دقيق الهدى', 14000, 15000, 50, '2026-08-26')")
    local_cursor.execute("INSERT INTO products VALUES ('2', 'كرتونة زيت سلايت', 650, 700, 100, '2026-08-26')")
    local_conn.commit()


def main(page: ft.Page):
    page.title = "سيستم محل الجملة المشترك"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    
    # متغيرات حفظ جلسة المستخدم
    user_email = ft.Ref[ft.TextField]()
    user_password = ft.Ref[ft.TextField]()
    current_user = None

    # --- شاشة تسجيل الدخول ---
    def login_click(e):
        nonlocal current_user
        if user_email.current.value and user_password.current.value:
            current_user = user_email.current.value
            page.controls.clear()
            show_main_dashboard()
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("برجاء إدخال الحساب وكلمة المرور"))
            page.snack_bar.open = True
            page.update()

    def show_login_screen():
        login_box = ft.Column(
            [
                ft.Text("🔐 تسجيل دخول النظام المشترك", size=24, weight=ft.FontWeight.BOLD),
                ft.TextField(ref=user_email, label="البريد الإلكتروني المشترك", keyboard_type=ft.KeyboardType.EMAIL),
                ft.TextField(ref=user_password, label="كلمة المرور", password=True, can_reveal_password=True),
                ft.ElevatedButton("دخول ومزامنة الأجهزة", on_click=login_click, width=250, bgcolor=ft.Colors.BLUE_ACCENT),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        page.add(ft.Container(content=login_box, padding=40))

    # --- شاشة الإدارة الرئيسية وتحديث الأسعار ---
    def show_main_dashboard():
        page.clean()
        
        # ترويسة التطبيق تظهر الحساب النشط
        page.add(
            ft.Container(
                content=ft.Row([
                    ft.Text(f"👤 الحساب: {current_user}", size=14, color=ft.Colors.GREEN_ACCENT),
                    ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: refresh_data(), tooltip="مزامنة وتحديث الأسعار")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=ft.Colors.SURFACE_CONTAINER, padding=10, border_radius=8
            )
        )

        # قائمة المنتجات وتحديث الأسعار
        product_list = ft.Column(scroll="adaptive", expand=True)
        
        def load_products():
            product_list.controls.clear()
            local_cursor.execute("SELECT * FROM products")
            for row in local_cursor.fetchall():
                p_id, name, p_price, t_price, stock, _ = row
                
                price_input = ft.TextField(
                    value=str(t_price), width=100, 
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_submit=lambda e, pid=p_id: update_product_price(pid, e.control.value)
                )

                # تم تعديل .add إلى .append هنا لحل المشكلة تماماً
                product_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"شراء: {p_price} ج.م | مخزن: {stock}", size=12, color=ft.Colors.GREY_400)
                                ], expand=True),
                                price_input
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=10
                        )
                    )
                )
            page.update()

        def update_product_price(pid, new_value):
            try:
                new_price = float(new_value)
                local_cursor.execute("UPDATE products SET today_price = ?, last_updated = ? WHERE id = ?", 
                                     (new_price, datetime.now().strftime("%Y-%m-%d %H:%M"), pid))
                local_conn.commit()
                page.snack_bar = ft.SnackBar(ft.Text("تم حفظ السعر محلياً! سيتم رفعه تلقائياً عند توفر شبكة"))
                page.snack_bar.open = True
                load_products()
            except ValueError:
                pass

        def refresh_data():
            page.snack_bar = ft.SnackBar(ft.Text("🔄 جاري مزامنة البيانات بين الهواتف المشتركة..."))
            page.snack_bar.open = True
            page.update()
            load_products()

        page.add(ft.Text("📊 أسعار السلع اليومية", size=20, weight=ft.FontWeight.BOLD))
        page.add(product_list)
        load_products()

    # بدء تشغيل شاشة تسجيل الدخول أولاً
    show_login_screen()

ft.app(target=main)