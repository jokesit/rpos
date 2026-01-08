# dining/views.py
from django.shortcuts import render, get_object_or_404
from restaurants.models import Restaurant, Table



def dining_menu(request, shop_slug, table_uuid):
    # 1. ตรวจสอบความถูกต้องของร้านและโต๊ะ
    restaurant = get_object_or_404(Restaurant, slug=shop_slug, is_active=True)
    table = get_object_or_404(Table, uuid=table_uuid, restaurant=restaurant)

    # 2. เก็บข้อมูลลง Session (เสมือนการ Login ชั่วคราว เพื่อให้รู้ว่า User นี้คือโต๊ะไหน)
    request.session['dining_table_id'] = table.id
    request.session['dining_restaurant_id'] = restaurant.id
    
    # 3. ดึงเมนูมาแสดง
    # กรองเฉพาะหมวดหมู่ที่มีเมนูที่เปิดขายอยู่ (is_available=True)
    categories = restaurant.categories.prefetch_related('items').filter(items__is_available=True).distinct()
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'categories': categories,
    }
    return render(request, 'dining/menu_public.html', context)