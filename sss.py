import flet as ft
import sqlite3
from datetime import datetime

# --- إعداد وإصلاح قاعدة البيانات والجداول المحاسبية الشاملة ---
local_conn = sqlite3.connect("local_gomla.db", check_same_thread=False)
local_cursor = local_conn.cursor()

local_cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, store_name TEXT)''')
local_cursor.execute('''CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, purchase_price REAL, today_price REAL, stock INTEGER, last_updated TEXT)''')
local_cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, price REAL, updated_at TEXT)''')
local_cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, phone TEXT, balance REAL)''')
local_cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, account_name TEXT, total REAL, date TEXT, month TEXT)''')
local_conn.commit()

def main(page: ft.Page):
    page.title = "سيستم محل الجملة المطور"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 20
    
    active_email = ""

    def refresh_all_views():
        page.clean()
        show_main_dashboard()

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
                return
            
            local_cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            if local_cursor.fetchone():
                local_cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
                if local_cursor.fetchone():
                    active_email = email
                    show_main_dashboard()
            else:
                store = store_input.value.strip() if store_input.value else "محل الجملة"
                local_cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (email, password, store))
                local_conn.commit()
                active_email = email
                show_main_dashboard()

        auth_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("🔐 نظام إدارة الجملة المشترك والربط السحابي", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    email_input, pass_input, store_input,
                    ft.ElevatedButton("دخول / تفعيل الحساب ومزامنة الأجهزة", on_click=login_logic, bgcolor=ft.Colors.BLUE_ACCENT, color=ft.Colors.WHITE, width=400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=25
            )
        )
        page.add(ft.Row([auth_card], alignment=ft.MainAxisAlignment.CENTER))
        page.update()

    def show_main_dashboard():
        page.clean()
        header = ft.Container(
            content=ft.Row([
                ft.Text(f"🟢 الحساب النشط والمزامن: {active_email}", color=ft.Colors.GREEN_ACCENT, weight=ft.FontWeight.W_500),
                ft.ElevatedButton("خروج", on_click=lambda e: show_auth_screen(), bgcolor=ft.Colors.RED_800, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor=ft.Colors.SURFACE_CONTAINER, padding=12, border_radius=8
        )
        page.add(header)

        # دالة تحديث وحفظ الأسعار اليومية والتاريخية
        def update_price(pid, val):
            try:
                new_p = float(val)
                local_cursor.execute("UPDATE products SET today_price=? WHERE id=?", (new_p, pid))
                local_cursor.execute("INSERT INTO price_history (product_id, price, updated_at) VALUES (?, ?, ?)", (pid, new_p, datetime.now().strftime("%Y-%m-%d %H:%M")))
                local_conn.commit()
                refresh_all_views()
            except: pass

        def delete_product(pid):
            local_cursor.execute("DELETE FROM products WHERE id=?", (pid,))
            local_conn.commit()
            refresh_all_views()

        # [1] عرض المنتجات وحذفها التلقائي المباشر
        prod_col = ft.Column()
        p_id = ft.TextField(label="كود السلعة", width=100)
        p_name = ft.TextField(label="اسم السلعة", expand=True)
        p_purch = ft.TextField(label="سعر الشراء", width=100)
        p_sell = ft.TextField(label="سعر البيع", width=100)
        p_stock = ft.TextField(label="الكمية", width=100)
        
        def add_prod(e):
            if p_id.value and p_name.value:
                local_cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?, ?)", (p_id.value, p_name.value, float(p_purch.value or 0), float(p_sell.value or 0), int(p_stock.value or 0), datetime.now().strftime("%Y-%m-%d")))
                local_cursor.execute("INSERT INTO price_history (product_id, price, updated_at) VALUES (?, ?, ?)", (p_id.value, float(p_sell.value or 0), datetime.now().strftime("%Y-%m-%d %H:%M")))
                local_conn.commit()
                refresh_all_views()

        prod_col.controls.append(ft.Row([p_id, p_name, p_purch, p_sell, p_stock, ft.IconButton(ft.Icons.ADD_BOX, on_click=add_prod, icon_color=ft.Colors.GREEN_ACCENT)]))
        
        local_cursor.execute("SELECT * FROM products")
        for r in local_cursor.fetchall():
            pid, name, purch, sell, stock, _ = r
            price_field = ft.TextField(value=str(sell), width=90, on_submit=lambda e, item_id=pid: update_price(item_id, e.control.value))
            prod_col.controls.append(ft.Card(content=ft.Container(content=ft.Row([ft.Column([ft.Text(f"📦 {name} (كود: {pid})"), ft.Text(f"شراء: {purch} | المخزن: {stock}", size=11, color=ft.Colors.GREY_400)], expand=True), ft.Row([ft.Text("سعر اليوم:"), price_field, ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_ACCENT, on_click=lambda e, item_id=pid: delete_product(item_id))])]), padding=10)))

        # [2] مرجعية الأسعار التاريخية لجميع الأيام السابقة
        hist_col = ft.Column()
        local_cursor.execute("SELECT p.name, h.price, h.updated_at FROM price_history h JOIN products p ON h.product_id = p.id ORDER BY h.id DESC")
        for r in local_cursor.fetchall():
            hist_col.controls.append(ft.ListTile(leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.ORANGE_ACCENT), title=ft.Text(f"تغير سعر [{r[0]}] إلى {r[1]} ج.م"), subtitle=ft.Text(f"التوقيت: {r[2]}")))

        # [3] أرشيف الفواتير وتخصيص الجزء المرجعي شهرياً تاريخياً
        inv_col = ft.Column()
        i_type = ft.Dropdown(options=[ft.dropdown.Option("بيع"), ft.dropdown.Option("شراء")], width=110, value="بيع")
        i_acc = ft.TextField(label="الطرف الثاني (العميل/المورد)", expand=True)
        i_total = ft.TextField(label="الإجمالي", width=120)
        
        def add_inv(e):
            if i_acc.value and i_total.value:
                now = datetime.now()
                local_cursor.execute("INSERT INTO invoices (type, account_name, total, date, month) VALUES (?, ?, ?, ?, ?)", (i_type.value, i_acc.value, float(i_total.value), now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")))
                local_conn.commit()
                refresh_all_views()

        inv_col.controls.append(ft.Row([i_type, i_acc, i_total, ft.ElevatedButton("حفظ", on_click=add_inv)]))
        local_cursor.execute("SELECT DISTINCT month FROM invoices ORDER BY month DESC")
        for m in local_cursor.fetchall():
            month_box = ft.Column()
            local_cursor.execute("SELECT type, account_name, total, date FROM invoices WHERE month=?", (m[0],))
            for inv in local_cursor.fetchall():
                month_box.controls.append(ft.Text(f"📅 {inv[3]} | {inv[0]} - الطرف: {inv[1]} | القيمة: {inv[2]} ج.م", color=ft.Colors.GREEN_ACCENT if inv[0]=="بيع" else ft.Colors.RED_ACCENT))
            inv_col.controls.append(ft.ExpansionTile(title=ft.Text(f"📁 فواتير شهر: {m[0]}", color=ft.Colors.BLUE_200), controls=[month_box]))

        # [4] جدول المحاسبة المالي للديون والفلوس (الموردين والعملاء)
        acc_col = ft.Column()
        a_name = ft.TextField(label="الاسم", expand=True)
        a_type = ft.Dropdown(options=[ft.dropdown.Option("عميل"), ft.dropdown.Option("مورد")], value="عميل", width=110)
        a_bal = ft.TextField(label="الرصيد الافتتاحي", width=130, value="0")
        
        def add_acc(e):
            if a_name.value:
                bal = float(a_bal.value)
                if a_type.value == "مورد" and bal > 0: bal = -bal
                local_cursor.execute("INSERT INTO accounts (name, type, phone, balance) VALUES (?, ?, '', ?)", (a_name.value, a_type.value, bal))
                local_conn.commit()
                refresh_all_views()

        acc_col.controls.append(ft.Row([a_name, a_type, a_bal, ft.IconButton(ft.Icons.PERSON_ADD, on_click=add_acc, icon_color=ft.Colors.BLUE_ACCENT)]))
        table = ft.DataTable(columns=[ft.DataColumn(ft.Text("الاسم")), ft.DataColumn(ft.Text("الفئة")), ft.DataColumn(ft.Text("الرصيد")), ft.DataColumn(ft.Text("الحالة المالية"))], rows=[])
        local_cursor.execute("SELECT name, type, balance FROM accounts")
        for r in local_cursor.fetchall():
            table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(r[0])), ft.DataCell(ft.Text(r[1])), ft.DataCell(ft.Text(str(abs(r[2])))), ft.DataCell(ft.Text("مدين (عليه فلوس)" if r[2]>0 else "دائن (ليه فلوس)" if r[2]<0 else "خالص", color=ft.Colors.GREEN_400 if r[2]>0 else ft.Colors.RED_400 if r[2]<0 else ft.Colors.GREY_400))]))
        acc_col.controls.append(ft.Row([table], scroll="always"))

        # ربط شاشات التبويبات بالسيستم الأساسي الموحد لضمان الاستقرار
