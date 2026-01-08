from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Restaurant, Table, Category, MenuItem # import เพิ่ม
from .forms import RestaurantForm, CategoryForm, MenuItemForm
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from decimal import Decimal
from django.utils import timezone


# for show owner
@login_required
def dashboard(request):
    # เช็คว่ามีร้านหรือยัง
    try:
        restaurant = request.user.restaurant
        # ถ้ามีร้านแล้ว ให้ไปหน้าจัดการ (ตอนนี้โชว์ชื่อร้านไปก่อน)
        return render(request, 'restaurants/dashboard.html', {'restaurant': restaurant})
    except Restaurant.DoesNotExist:
        # ถ้ายังไม่มีร้าน ให้ไปหน้าสร้างร้าน
        return redirect('create_restaurant')

@login_required
def create_restaurant(request):
    # ป้องกันคนที่มีร้านแล้ว แอบมาเข้าหน้านี้
    if hasattr(request.user, 'restaurant'):
        return redirect('dashboard')

    if request.method == 'POST':
        form = RestaurantForm(request.POST)
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
def menu_manage(request):
    restaurant = request.user.restaurant
    categories = restaurant.categories.prefetch_related('items').all() # ดึงหมวดหมู่พร้อมรายการอาหาร
    
    return render(request, 'restaurants/menu_manage.html', {
        'restaurant': restaurant,
        'categories': categories
    })

@login_required
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
def table_bill_detail(request, table_id):
    restaurant = request.user.restaurant
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    # 1. ดึงออเดอร์ที่ยังไม่จ่าย (Active Orders)
    # เราไม่เอาที่ CANCELLED
    active_orders = table.orders.filter(is_paid=False).exclude(status='CANCELLED')
    
    if not active_orders.exists():
        messages.warning(request, 'โต๊ะนี้ไม่มีรายการค้างชำระ')
        return redirect('cashier_dashboard')

    # 2. รวบรวมรายการอาหารทั้งหมด (Order Items) จากทุกออเดอร์
    # เรียงตามเวลาสั่ง (เก่า -> ใหม่)
    order_items = []
    subtotal = Decimal('0.00')
    
    for order in active_orders:
        for item in order.items.all():
            item_total = item.price * item.quantity
            subtotal += item_total
            order_items.append({
                'menu_name': item.menu_item.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item_total,
                'order_time': order.created_at,
                'status': order.status
            })

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

    context = {
        'restaurant': restaurant,
        'table': table,
        'order_items': order_items,
        'subtotal': subtotal,
        'service_charge_amount': service_charge_amount,
        'vat_amount': vat_amount,
        'grand_total': grand_total,
        'active_orders': active_orders,
    }
    
    return render(request, 'restaurants/bill_detail.html', context)


@login_required
def close_bill(request, table_id):
    if request.method == 'POST':
        restaurant = request.user.restaurant
        table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
        
        # ดึงออเดอร์ที่ยังไม่จ่ายทั้งหมดมาปิด
        active_orders = table.orders.filter(is_paid=False).exclude(status='CANCELLED')
        
        if active_orders.exists():
            # Update ทีเดียวทุก Rows (Bulk Update)
            active_orders.update(
                is_paid=True, 
                status='COMPLETED',
                updated_at=timezone.now()
            )
            
            # (Optional) ถ้า Model Table มี field is_occupied ให้เคลียร์ด้วย
            # table.is_occupied = False
            # table.save()
            
            messages.success(request, f'รับชำระเงินโต๊ะ {table.name} เรียบร้อยแล้ว')
        
    return redirect('cashier_dashboard')

# ------

# for report
@login_required
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


