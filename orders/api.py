# orders/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from restaurants.models import Table, MenuItem
from .models import Order, OrderItem
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@csrf_exempt
def create_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 1. รับข้อมูล
            table_uuid = data.get('table_uuid')
            cart_items = data.get('cart') 
            
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
            for item_data in cart_items:
                # ใช้ try-except กันกรณี Menu ID ผิดพลาดหรือถูกลบไปแล้ว
                try:
                    menu_item = MenuItem.objects.get(id=item_data['id'])
                except MenuItem.DoesNotExist:
                    continue # ข้ามรายการที่หาไม่เจอ

                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['qty'],
                    price=menu_item.price, # Snapshot ราคา
                    note=item_data.get('note', '')
                )
                total_price += (menu_item.price * item_data['qty'])
            
            # 5. อัปเดตราคารวม
            order.total_price = total_price
            order.save()

            # ==========================================================
            # ⭐ ADD THIS: ส่ง Real-time Notification
            # ==========================================================
            
            # ดึงรายการอาหารที่เพิ่งสร้าง เพื่อส่งไปแสดงผล (ใช้ select_related เพื่อลด query)
            # หมายเหตุ: ใช้ order.orderitem_set.all() เว้นแต่ใน models.py คุณตั้ง related_name='items'
            created_items = order.items.select_related('menu_item').all()
            
            item_list = [
                f"{item.menu_item.name} x{item.quantity}" 
                for item in created_items
            ]

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'restaurant_{restaurant.id}',
                {
                    'type': 'order_notification',
                    'message': 'New Order Received',
                    'order': {
                        'id': order.id,
                        'table': table.name,
                        'total_price': float(order.total_price),
                        'items': item_list,
                        'created_at': order.created_at.strftime('%H:%M')
                    }
                }
            )
            
            return JsonResponse({'success': True, 'order_id': order.id})
            
        except Exception as e:
            # Print error ลง console เพื่อให้ debug ง่ายขึ้นเวลาเจอ 500
            print(f"Error creating order: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')
            
            order = get_object_or_404(Order, id=order_id)
            
            order.status = new_status
            order.save()
            
            # (Optional) ส่ง WebSocket บอก Dashboard ให้รีเฟรชสถานะด้วยก็ได้
            # เพื่อให้แคชเชียร์คนอื่นเห็นว่า ออเดอร์นี้เปลี่ยนสถานะแล้ว
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'restaurant_{order.restaurant.id}',
                {
                    'type': 'order_notification', # ใช้ type เดิมหรือสร้างใหม่ก็ได้
                    'message': 'Order Updated',
                    'order': {
                        'id': order.id,
                        'status': new_status,
                        # ส่งข้อมูลแค่นี้พอเพื่อให้ Frontend รู้ว่าต้องรีเฟรช
                        'refresh_only': True 
                    }
                }
            )
            
            return JsonResponse({'success': True, 'status': new_status})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)