# orders/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from restaurants.models import Restaurant, Table, MenuItem
from .models import Order, OrderItem
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@csrf_exempt # ใช้ชั่วคราวเพื่อให้เทสง่าย (Production ควรใช้ CSRF Token ผ่าน Header)
def create_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 1. ดึงข้อมูลจาก Session หรือจาก Data ที่ส่งมา
            table_uuid = data.get('table_uuid')
            cart_items = data.get('cart') # Array [{id, qty, note}, ...]
            
            if not table_uuid or not cart_items:
                return JsonResponse({'error': 'ข้อมูลไม่ครบถ้วน'}, status=400)

            # 2. ตรวจสอบโต๊ะ
            table = get_object_or_404(Table, uuid=table_uuid)
            restaurant = table.restaurant
            
            # 3. สร้าง Order Header
            order = Order.objects.create(
                restaurant=restaurant,
                table=table,
                status='PENDING',
                session_id=request.session.session_key or ''
            )
            
            total_price = 0
            
            # 4. วนลูปสร้าง Order Items
            for item in cart_items:
                menu_item = MenuItem.objects.get(id=item['id'])
                
                # บันทึกราคา ณ ตอนที่สั่ง (Snapshot price)
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['qty'],
                    price=menu_item.price, 
                    note=item.get('note', '')
                )
                total_price += (menu_item.price * item['qty'])
            
            # 5. อัปเดตราคารวม
            order.total_price = total_price
            order.save()


            # ⭐ ADD THIS: ส่ง Real-time Notification ⭐
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'restaurant_{restaurant.id}', # ส่งเข้าห้องของร้านนั้นๆ
                {
                    'type': 'order_notification', # ชื่อฟังก์ชันใน consumers.py
                    'message': 'New Order Received',
                    'order': {
                        'id': order.id,
                        'table': table.name,
                        'total_price': float(order.total_price),
                        'items': [
                            f"{item.menu_item.name} x{item.quantity}" 
                            for item in order.items.all()
                        ],
                        'created_at': order.created_at.strftime('%H:%M')
                    }
                }
            )
            
            return JsonResponse({'success': True, 'order_id': order.id})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)



@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status') # 'COOKING' หรือ 'SERVED'
            
            order = get_object_or_404(Order, id=order_id)
            
            # อัปเดตสถานะ
            order.status = new_status
            order.save()
            
            # (Optional) ตรงนี้เราสามารถส่ง WebSocket กลับไปบอกลูกค้าได้ว่า "อาหารกำลังทำ"
            
            return JsonResponse({'success': True, 'status': new_status})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)