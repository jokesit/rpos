import datetime
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Table, Category, MenuItem, Restaurant
from .forms import RestaurantForm, CategoryForm, MenuItemForm, RestaurantSettingsForm, PromoImageFormSet
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncHour
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from orders.models import OrderItem
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from .decorators import restaurant_active_required
from django.core.paginator import Paginator
from django.http import JsonResponse



@user_passes_test(lambda u: u.is_superuser) # เฉพาะ Superuser เท่านั้น
def superuser_dashboard(request):
    restaurants = Restaurant.objects.all().order_by('-created_at')
    
    context = {
        'restaurants': restaurants,
        'total_count': restaurants.count(),
        'active_count': restaurants.filter(is_active=True).count()
    }
    return render(request, 'superuser/dashboard.html', context)


@require_POST
@user_passes_test(lambda u: u.is_superuser)
def toggle_restaurant_active(request, restaurant_id):
    shop = get_object_or_404(Restaurant, pk=restaurant_id)
    shop.is_active = not shop.is_active # สลับสถานะ
    shop.save()
    
    status_msg = "เปิดใช้งาน" if shop.is_active else "ระงับการใช้งาน"
    messages.success(request, f"ร้าน {shop.name} ถูก {status_msg} แล้ว")
    return redirect('superuser_dashboard')


# for show owner
@login_required
@restaurant_active_required
def dashboard(request):
    # เช็คว่าเป็น Superuser หรือไม่?
    if request.user.is_superuser:
        # ถ้าใช่ ให้ไปหน้า Admin Panel ของ Django เลย
        return redirect('/super-admin/')
    
    # 2. เช็คว่า User นี้มีร้านค้าหรือยัง?
    try:
        restaurant = request.user.restaurant
    except ObjectDoesNotExist:
        # ถ้ายังไม่มีร้าน ให้ไปหน้าสร้างร้าน (เดี๋ยวเราสร้าง view นี้ในขั้นตอนต่อไป)
        return redirect('create_restaurant')
    

    today = timezone.now().date()

    # 1. ยอดขายวันนี้ (เฉพาะที่จ่ายเงินแล้ว)
    today_sales = restaurant.orders.filter(
        created_at__date=today, 
        is_paid=True
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # 2. จำนวนออเดอร์วันนี้
    today_orders_count = restaurant.orders.filter(created_at__date=today).count()

    # 3. ออเดอร์ที่รอครัวทำ (Pending/Cooking)
    pending_orders_count = restaurant.orders.filter(
        status__in=['PENDING', 'COOKING']
    ).count()

    # 4. โต๊ะที่กำลังใช้งาน (Active Tables)
    # นับโต๊ะที่มีออเดอร์ค้างชำระ
    active_tables_count = restaurant.tables.filter(
        orders__is_paid=False
    ).exclude(orders__status='CANCELLED').distinct().count()

    # 5. รายการล่าสุด 5 รายการ (Recent Activity)
    recent_orders = restaurant.orders.order_by('-created_at')[:5]

    context = {
        'restaurant': restaurant,
        'today_sales': today_sales,
        'today_orders_count': today_orders_count,
        'pending_orders_count': pending_orders_count,
        'active_tables_count': active_tables_count,
        'recent_orders': recent_orders,
    }
    return render(request, 'restaurants/dashboard.html', context)

@login_required
def create_restaurant(request):
    # ป้องกันคนที่มีร้านแล้ว แอบมาเข้าหน้านี้
    if hasattr(request.user, 'restaurant'):
        return redirect('dashboard')

    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.owner = request.user
            restaurant.save()
            return redirect('dashboard')
    else:
        form = RestaurantForm()
    
    return render(request, 'restaurants/create.html', {'form': form})

# ------------------ 




# for manage table

@login_required
@restaurant_active_required
def table_list(request):
    restaurant = request.user.restaurant
    tables = restaurant.tables.all()
    
    # Logic เพิ่มโต๊ะแบบง่ายๆ ในหน้าเดียวกันเลย
    if request.method == 'POST':
        table_name = request.POST.get('name')
        if table_name:
            Table.objects.create(restaurant=restaurant, name=table_name)
            messages.success(request, f'เพิ่มโต๊ะ {table_name} เรียบร้อยแล้ว')
            return redirect('table_list')
            
    return render(request, 'restaurants/table_list.html', {'tables': tables, 'restaurant': restaurant})

@login_required
@restaurant_active_required
def delete_table(request, table_id):
    restaurant = request.user.restaurant
    # ต้องเช็คว่า table_id นี้เป็นของร้านเราจริงๆ (Security Check)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    if request.method == 'POST':
        table.delete()
        messages.success(request, 'ลบโต๊ะเรียบร้อยแล้ว')
        
    return redirect('table_list')

# ----------------


# for create menu

@login_required
@restaurant_active_required
def menu_manage(request):
    restaurant = request.user.restaurant
    categories = restaurant.categories.prefetch_related('items').all() # ดึงหมวดหมู่พร้อมรายการอาหาร
    
    return render(request, 'restaurants/menu_manage.html', {
        'restaurant': restaurant,
        'categories': categories
    })

@login_required
@restaurant_active_required
def add_category(request):
    restaurant = request.user.restaurant
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant
            category.save()
            messages.success(request, 'เพิ่มหมวดหมู่สำเร็จ')
            return redirect('menu_manage')
    else:
        form = CategoryForm()
    return render(request, 'restaurants/form_generic.html', {'form': form, 'title': 'เพิ่มหมวดหมู่'})

@login_required
@restaurant_active_required
def add_menu_item(request):
    restaurant = request.user.restaurant
    if request.method == 'POST':
        # ส่ง restaurant เข้าไปใน form เพื่อกรอง category
        form = MenuItemForm(request.POST, request.FILES, restaurant=restaurant) 
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มเมนูสำเร็จ')
            return redirect('menu_manage')
    else:
        form = MenuItemForm(restaurant=restaurant)
    return render(request, 'restaurants/form_generic.html', {'form': form, 'title': 'เพิ่มเมนูอาหาร'})


@login_required
@restaurant_active_required
def edit_menu_item(request, item_id):
    restaurant = request.user.restaurant
    
    # ดึงเมนู โดยเช็คว่า category ของเมนูนั้น ต้องเป็นของร้านเราจริงๆ
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
    
    if request.method == 'POST':
        # ส่ง instance=item เข้าไป เพื่อบอกว่านี่คือการ "แก้ไข" ไม่ใช่สร้างใหม่
        form = MenuItemForm(request.POST, request.FILES, instance=item, restaurant=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, f'แก้ไขเมนู "{item.name}" เรียบร้อยแล้ว')
            return redirect('menu_manage')
    else:
        # โหลดข้อมูลเดิมมาใส่ในฟอร์ม
        form = MenuItemForm(instance=item, restaurant=restaurant)
        
    return render(request, 'restaurants/form_generic.html', {
        'form': form, 
        'title': f'แก้ไขเมนู: {item.name}'
    })


@login_required
@restaurant_active_required
def delete_menu_item(request, item_id):
    restaurant = request.user.restaurant
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
    
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'ลบเมนู "{item_name}" แล้ว')
        
    return redirect('menu_manage')


# (แถม) แก้ไขหมวดหมู่ด้วย เผื่อพิมพ์ผิด
@login_required
@restaurant_active_required
def edit_category(request, category_id):
    restaurant = request.user.restaurant
    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขหมวดหมู่เรียบร้อย')
            return redirect('menu_manage')
    else:
        form = CategoryForm(instance=category)
        
    return render(request, 'restaurants/form_generic.html', {'form': form, 'title': 'แก้ไขหมวดหมู่'})

@login_required
@restaurant_active_required
def delete_category(request, category_id):
    restaurant = request.user.restaurant
    category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
    
    if request.method == 'POST':
        category.delete() # เมนูในหมวดนี้จะหายไปด้วย (Cascade)
        messages.success(request, 'ลบหมวดหมู่เรียบร้อย')
        
    return redirect('menu_manage')

# ----------


# for kitchen

@login_required
@restaurant_active_required
def kitchen_dashboard(request):
    restaurant = request.user.restaurant
    # ดึงออเดอร์ที่ยังทำไม่เสร็จ (Pending/Cooking)
    orders = restaurant.orders.filter(status__in=['PENDING', 'COOKING']).order_by('created_at')

    return render(request, 'restaurants/kitchen_dashboard.html', {
        'restaurant': restaurant,
        'orders': orders
    })


# -----------


# for cashier

@login_required
@restaurant_active_required
def cashier_dashboard(request):
    restaurant = request.user.restaurant
    tables = restaurant.tables.all()
    
    # ดึงข้อมูลมาแปะใส่ table object ว่าโต๊ะนี้มียอดค้างเท่าไหร่
    for table in tables:
        # หาออเดอร์ที่ยังไม่จ่ายเงิน (is_paid=False) และยังไม่ยกเลิก
        active_orders = table.orders.filter(is_paid=False).exclude(status='CANCELLED')
        
        if active_orders.exists():
            table.has_active_order = True
            table.pending_amount = active_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            table.order_count = active_orders.count()
        else:
            table.has_active_order = False
            
    return render(request, 'restaurants/cashier_dashboard.html', {
        'restaurant': restaurant,
        'tables': tables
    })


@login_required
@restaurant_active_required
def table_bill_detail(request, table_id):
    restaurant = request.user.restaurant
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    # 1. ดึงออเดอร์ที่ยังไม่จ่าย (Active Orders)
    # เราไม่เอาที่ CANCELLED
    active_orders = table.orders.filter(is_paid=False).exclude(status='CANCELLED').order_by('created_at')
    
    if not active_orders.exists():
        messages.warning(request, 'โต๊ะนี้ไม่มีรายการค้างชำระ')
        return redirect('cashier_dashboard')

    # =========================================================
    # ⭐ 2. รวบรวมและรวมรายการอาหาร (Aggregation Logic) ⭐
    # =========================================================
    aggregated_items = {}
    subtotal = Decimal('0.00')
    
    for order in active_orders:
        for item in order.items.select_related('menu_item').all():
            # คำนวณยอดเงินของ item นี้
            item_total = item.price * item.quantity
            
            # บวกยอดรวมทันที
            subtotal += item_total
            
            # สร้าง Key สำหรับการรวม (ใช้ ID เมนู และ ราคา)
            # ถ้าราคาเปลี่ยน ต้องแยกบรรทัด เพื่อความถูกต้องทางบัญชี
            key = (item.menu_item.id, item.price)

            if key in aggregated_items:
                # ถ้ามีรายการนี้อยู่แล้ว ให้บวกจำนวนเพิ่ม
                aggregated_items[key]['quantity'] += item.quantity
                aggregated_items[key]['total'] += item_total
                
                # อัปเดตข้อมูลล่าสุด (เพื่อให้เวลาลบ จะลบตัวล่าสุดก่อน LIFO)
                aggregated_items[key]['id'] = item.id 
                aggregated_items[key]['status'] = order.status
                aggregated_items[key]['order_time'] = order.created_at
            else:
                # ถ้ายังไม่มี ให้สร้างใหม่
                aggregated_items[key] = {
                    'id': item.id, # ID สำหรับใช้ลบ (Delete Item)
                    'menu_name': item.menu_item.name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'total': item_total,
                    'order_time': order.created_at,
                    'status': order.status
                }

    # แปลง Dictionary กลับเป็น List เพื่อส่งให้ Template วนลูป
    order_items = list(aggregated_items.values())

    # 3. คำนวณภาษีและ Service Charge
    # แปลงค่า Default 0 ให้เป็น Decimal('0') เพื่อไม่ให้กลายเป็น Float
    service_charge_percent = restaurant.service_charge_percent or Decimal('0')
    vat_percent = restaurant.vat_percent or Decimal('0')
    
    # ใช้ Decimal('100') ในการหาร เพื่อบังคับให้ผลลัพธ์เป็น Decimal เสมอ
    service_charge_amount = subtotal * (service_charge_percent / Decimal('100'))
    
    # รวมยอดก่อน VAT
    after_service = subtotal + service_charge_amount
    
    # คำนวณ VAT
    vat_amount = after_service * (vat_percent / Decimal('100'))
    
    # ยอดสุทธิ
    grand_total = after_service + vat_amount

    # ⭐ 4. สร้างเลขที่บิล (Bill Number) ⭐
    # ใช้ ID ของออเดอร์แรกสุดเป็นเลขที่บิลหลัก
    # หรือถ้าไม่มีออเดอร์เลย ให้เป็น "-"
    first_order = active_orders.first() # query set นี้ order_by created_at มาแล้ว
    
    if first_order:
        # แปลงเป็นเวลาท้องถิ่นก่อน (เพื่อให้ได้วันที่ที่ถูกต้องของไทย)
        local_created_at = timezone.localtime(first_order.created_at)
        
        # จัดรูปแบบ: YYYYMMDD-ID (เช่น 20260123-89)
        date_str = local_created_at.strftime('%Y%m%d')
        bill_number = f"{date_str}-{first_order.id}"
    else:
        bill_number = "-"

    context = {
        'restaurant': restaurant,
        'table': table,
        'order_items': order_items,
        'subtotal': subtotal,
        'service_charge_amount': service_charge_amount,
        'vat_amount': vat_amount,
        'grand_total': grand_total,
        'active_orders': active_orders,
        'bill_number': bill_number,
    }
    
    return render(request, 'restaurants/bill_detail.html', context)


@login_required
@restaurant_active_required
def close_bill(request, table_id):
    if request.method == 'POST':
        restaurant = request.user.restaurant
        table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
        
        # 1. ✅ รับค่าวิธีชำระเงินจาก Form (ถ้าไม่ส่งมา ให้ Default เป็น CASH)
        payment_method = request.POST.get('payment_method', 'CASH')
        
        # ดึงออเดอร์ที่ยังไม่จ่ายทั้งหมดมาปิด
        active_orders = table.orders.filter(is_paid=False).exclude(status='CANCELLED')
        
        if active_orders.exists():
            # 2. ✅ Update ข้อมูลรวมถึง payment_method ทีเดียวทุก Rows (Bulk Update)
            active_orders.update(
                is_paid=True, 
                status='COMPLETED',
                payment_method=payment_method, # บันทึกว่าจ่ายด้วยอะไร (CASH/QR)
                updated_at=timezone.now()
            )
            
            # รีเซ็ต UUID โต๊ะ เพื่อให้ Link เก่าใช้ไม่ได้ (ลูกค้าใหม่ต้องสแกนใหม่)
            table.refresh_uuid()
            
            # 3. ส่งสัญญาณ WebSocket
            channel_layer = get_channel_layer()
            
            # 3.1 สั่งให้หน้าจอ Cashier รีเฟรช (เพื่อเอาโต๊ะออกจาก Dashboard)
            async_to_sync(channel_layer.group_send)(
                f'restaurant_{table.restaurant.id}',
                {
                    'type': 'table_update_notification',
                    'message': 'Refresh Tables'
                }
            )
            
            # 3.2 (Optional) สั่งให้หน้าจอลูกค้าปิดหน้าต่างจ่ายเงิน (ถ้าเปิดค้างไว้)
            async_to_sync(channel_layer.group_send)(
                f'restaurant_{table.restaurant.id}', 
                {
                    'type': 'hide_customer_payment', # ต้องไปดักใน consumers.py ถ้าต้องการ
                    'command': 'hide_customer_payment'
                }
            )
            
            messages.success(request, f'รับชำระเงินโต๊ะ {table.name} เรียบร้อย ({payment_method})')
        
    return redirect('cashier_dashboard')

# ------

# for report
@login_required
@restaurant_active_required
def report_sales(request):
    restaurant = request.user.restaurant
    
    # ดึงออเดอร์ที่จ่ายเงินแล้ว (COMPLETED)
    completed_orders = restaurant.orders.filter(status='COMPLETED', is_paid=True)
    
    # 1. ยอดขายวันนี้
    today = timezone.now().date()
    today_sales = completed_orders.filter(created_at__date=today).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # 2. ยอดขายย้อนหลัง 7 วัน (Group by Date)
    daily_sales = completed_orders.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(total=Sum('total_price'), count=Count('id')) \
        .order_by('-date')[:7] # เอาแค่ 7 วันล่าสุด

    return render(request, 'restaurants/report_sales.html', {
        'restaurant': restaurant,
        'today_sales': today_sales,
        'daily_sales': daily_sales
    })

# ----------

# setting

@login_required
@restaurant_active_required
def restaurant_settings(request):
    restaurant = request.user.restaurant
    
    if request.method == 'POST':
        # ส่ง request.user ไปให้ Form ด้วย
        form = RestaurantSettingsForm(request.POST, request.FILES, instance=restaurant, user=request.user)
        # รับค่า Formset
        formset = PromoImageFormSet(request.POST, request.FILES, instance=restaurant)
        
        if form.is_valid() and formset.is_valid():
            # 1. บันทึกข้อมูลร้านค้า (Restaurant)
            form.save()
            formset.save() # บันทึกรูปสไลด์
            
            # 2. บันทึกข้อมูล Username (User)
            new_username = form.cleaned_data['username']
            user = request.user
            if user.username != new_username:
                user.username = new_username
                user.save()
            
            messages.success(request, 'บันทึกการตั้งค่าและชื่อผู้ใช้เรียบร้อยแล้ว')
            return redirect('restaurant_settings')
    else:
        # ส่ง request.user ไปให้ Form เพื่อแสดงค่าเริ่มต้น
        form = RestaurantSettingsForm(instance=restaurant, user=request.user)
        formset = PromoImageFormSet(instance=restaurant)
        
    return render(request, 'restaurants/settings.html', {
        'form': form,
        'formset': formset, # ส่งไป template
        'restaurant': restaurant
    })


# -------


@login_required
@restaurant_active_required
def customer_facing_display(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, owner=request.user)
    promo_images = restaurant.promo_images.all().order_by('-created_at')
    return render(request, 'restaurants/customer_display.html', {
        'restaurant': restaurant,
        'promo_images': promo_images,
    })



# delete item in bill
@login_required
@restaurant_active_required
def delete_order_item(request, item_id):
    item = get_object_or_404(
        OrderItem,
        pk=item_id,
        order__restaurant__owner=request.user
    )

    order = item.order

    if request.method == 'POST':
        item_total = item.price * item.quantity
        menu_name = item.menu_item.name

        # 1. ลบรายการ
        item.delete()

        # 2. อัปเดตยอดรวมของ Order
        order.total_price -= item_total
        if order.total_price < 0:
            order.total_price = 0
        order.save()

        messages.success(request, f"ลบรายการ {menu_name} เรียบร้อยแล้ว")

    return redirect('table_bill_detail', table_id=order.table.id)



def restaurant_suspended(request):
    return render(request, 'restaurants/suspended.html')




# data analyte
@login_required
@restaurant_active_required
def analytics_dashboard(request):
    restaurant = request.user.restaurant
    
    # 1. จัดการ Date Filter (Default = 30 วันย้อนหลัง)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    if start_date_str and end_date_str:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - datetime.timedelta(days=29) # 30 วันรวมวันนี้
        end_date = today

    # Base Query: ออเดอร์ที่จ่ายเงินแล้วในช่วงเวลานั้น
    orders = restaurant.orders.filter(
        status='COMPLETED',
        is_paid=True,
        created_at__date__range=[start_date, end_date]
    )

    # 2. Summary Cards (KPIs)
    total_revenue = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = orders.count()
    # AOV = Average Order Value (ยอดขายเฉลี่ยต่อบิล) สำคัญมากสำหรับเจ้าของ
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # 3. Sales Trend Graph (กราฟเส้นยอดขายรายวัน)
    daily_sales = orders.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(total=Sum('total_price'), count=Count('id')) \
        .order_by('date')
        
    # เตรียมข้อมูล JSON สำหรับ Chart.js
    chart_dates = [x['date'].strftime('%d/%m') for x in daily_sales]
    chart_revenues = [float(x['total']) for x in daily_sales]
    chart_orders = [x['count'] for x in daily_sales]

    # 4. Top Selling Items (รายการขายดี) - Join กับ OrderItem
    # ต้องดึง OrderItem ที่อยู่ใน Order เหล่านั้น
    top_items = OrderItem.objects.filter(order__in=orders) \
        .values('menu_item__name') \
        .annotate(total_qty=Sum('quantity'), total_sales=Sum(F('price') * F('quantity'))) \
        .order_by('-total_qty')[:10] # เอา 10 อันดับแรก

    top_items_labels = [x['menu_item__name'] for x in top_items]
    top_items_data = [x['total_qty'] for x in top_items]

    # 5. Peak Hours (ช่วงเวลาขายดี)
    peak_hours = orders.annotate(hour=TruncHour('created_at')) \
        .values('hour') \
        .annotate(count=Count('id')) \
        .order_by('hour')
        
    # แปลงข้อมูล Peak Hours ให้เป็น Format ง่ายๆ (00-23 นาฬิกา)
    # (ส่วนนี้อาจต้องทำ Logic เพิ่มใน Template หรือ JS เพื่อ map ชั่วโมงให้ครบ 24 ชม.)

    context = {
        'restaurant': restaurant,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        # Chart Data
        'chart_dates': json.dumps(chart_dates),
        'chart_revenues': json.dumps(chart_revenues),
        'top_items_labels': json.dumps(top_items_labels),
        'top_items_data': json.dumps(top_items_data),
        # Tables
        'top_items_list': top_items,
        'recent_orders': orders.order_by('-created_at')[:20] # 20 รายการล่าสุดในตาราง
    }

    return render(request, 'restaurants/analytics.html', context)


# --------

# show all order to admin


@login_required
@restaurant_active_required
def order_history(request):
    restaurant = request.user.restaurant
    
    # ดึงออเดอร์ที่จบแล้ว เรียงจากใหม่ -> เก่า
    orders_list = restaurant.orders.filter(
        status='COMPLETED', 
        is_paid=True
    ).order_by('-created_at')
    
    # แบ่งหน้า หน้าละ 50 รายการ
    paginator = Paginator(orders_list, 50) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'restaurants/order_history.html', {
        'restaurant': restaurant,
        'page_obj': page_obj
    })

# 2. API สำหรับดึงรายละเอียดบิล (เพื่อแสดงใน Modal)
@login_required
def get_order_details_api(request, order_id):
    try:
        # เช็คว่าเป็นออเดอร์ของร้านนี้จริงๆ (Security)
        order = request.user.restaurant.orders.get(id=order_id)
        
        items = []
        for item in order.items.all():
            items.append({
                'name': item.menu_item.name,
                'quantity': item.quantity,
                'price': float(item.price),
                'total': float(item.price * item.quantity)
            })
            
        return JsonResponse({
            'success': True,
            'id': order.id,
            'date': order.created_at.strftime('%d/%m/%Y %H:%M'),
            'table': order.table.name,
            'items': items,
            'total': float(order.total_price),
            'payment_method': getattr(order, 'payment_method', 'ไม่ระบุ') or 'เงินสด',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
# -----