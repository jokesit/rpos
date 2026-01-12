# dining/views.py
from django.shortcuts import render, get_object_or_404, redirect
from restaurants.models import Restaurant, Table, MenuItem
from django.db.models import Prefetch

def dining_menu(request, shop_slug, table_uuid):
    # 1. ค้นหาร้านค้าก่อน (ถ้าไม่เจอร้าน ให้ 404 ไปเลย อันนี้ถูกต้อง)
    restaurant = get_object_or_404(Restaurant, slug=shop_slug, is_active=True)

    # 2. ⭐ พยายามค้นหาโต๊ะด้วย UUID (จุดที่แก้ไข)
    try:
        table = Table.objects.get(uuid=table_uuid, restaurant=restaurant)
    except Table.DoesNotExist:
        # ⚠️ ถ้าหาไม่เจอ แปลว่า UUID ถูกเปลี่ยนไปแล้ว (ปิดโต๊ะแล้ว)
        # ให้ส่งไปหน้า "หมดเวลา / ขอบคุณ" แทน
        return render(request, 'dining/session_expired.html', {
            'restaurant': restaurant
        })

    # 3. เก็บข้อมูลลง Session
    request.session['dining_table_id'] = table.id
    request.session['dining_restaurant_id'] = restaurant.id
    
    # 4. ดึงเมนูมาแสดง (ปรับปรุง Query ให้ดีขึ้นเล็กน้อย)
    # ใช้ Prefetch เพื่อดึงเฉพาะ item ที่ is_available=True มาเตรียมไว้เลย
    # (ช่วยให้ตอน loop ใน template ไม่ต้องเช็ค if item.is_available อีกรอบ และลด query)
    items_prefetch = Prefetch('items', queryset=MenuItem.objects.filter(is_available=True))
    
    categories = restaurant.categories.filter(items__is_available=True)\
        .prefetch_related(items_prefetch)\
        .distinct()
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'categories': categories,
    }
    return render(request, 'dining/menu_public.html', context)