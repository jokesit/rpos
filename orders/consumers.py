# orders/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # ดึง restaurant_id จาก URL (เช่น ws/orders/1/)
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.room_group_name = f'restaurant_{self.restaurant_id}'

        # 1. เข้ากลุ่ม (Join room group)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # ออกจากกลุ่ม ป้องกัน memory leak
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # ฟังก์ชันรับข้อความจาก Group แล้วส่งต่อให้ Frontend (JavaScript)
    async def order_notification(self, event):
        message = event['message']
        order_data = event['order']

        # ส่ง JSON ไปหา Browser
        await self.send(text_data=json.dumps({
            'message': message,
            'order': order_data
        }))