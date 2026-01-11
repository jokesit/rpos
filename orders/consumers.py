# # orders/consumers.py
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class OrderConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # ดึง restaurant_id จาก URL (เช่น ws/orders/1/)
#         self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
#         print(f"✅ Restaurant ID: {self.restaurant_id}")
#         self.room_group_name = f'restaurant_{self.restaurant_id}'

#         print(f"🔵 Joining group: {self.room_group_name}")
#         # 1. เข้ากลุ่ม (Join room group)
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()
#         print("✅ WebSocket Connected Successfully!")

#     async def disconnect(self, close_code):
#         # ออกจากกลุ่ม ป้องกัน memory leak
#         try:
#             await self.channel_layer.group_discard(
#                 self.room_group_name,
#                 self.channel_name
#             )
#             print("🔴 Disconnected")
#         except:
#             print('error')
#             pass


#     # ⭐ ส่วนที่เพิ่มมาใหม่: รับข้อความจาก Client (หน้า Cashier) ⭐
#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             command = data.get('command')

#             # กรณีที่ 1: Cashier สั่งให้แสดงหน้าชำระเงินที่จอลูกค้า
#             if command == 'show_customer_payment':
#                 # กระจายข่าว (Broadcast) ไปบอกทุกคนในกลุ่ม (รวมถึงจอลูกค้า)
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {
#                         'type': 'show_customer_payment', # ชื่อ method ที่จะถูกเรียกด้านล่าง
#                         'items': data.get('items', []),
#                         'total': data.get('total', '0.00')
#                     }
#                 )

#             # กรณีที่ 2: Cashier สั่งให้ปิดหน้าชำระเงิน (กลับไปโชว์ Slide)
#             elif command == 'hide_customer_payment':
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {
#                         'type': 'hide_customer_payment'
#                     }
#                 )
                
#         except Exception as e:
#             print(f"Error in receive: {e}")

#     # ฟังก์ชันรับข้อความจาก Group แล้วส่งต่อให้ Frontend (JavaScript)
#     async def order_notification(self, event):
#         message = event['message']
#         order_data = event['order']

#         # ส่ง JSON ไปหา Browser
#         await self.send(text_data=json.dumps({
#             'type': 'order_notification',
#             'message': message,
#             'order': order_data
#         }))

#     # for seconds display
#     async def show_customer_payment(self, event):
#         # ส่งต่อข้อมูลไปให้ Frontend (Customer Display)
#         await self.send(text_data=json.dumps({
#             'type': 'show_customer_payment',
#             'items': event['items'],
#             'total': event['total']
#         }))

#     async def hide_customer_payment(self, event):
#         await self.send(text_data=json.dumps({
#             'type': 'hide_customer_payment'
#         }))


import json
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderConsumer(AsyncWebsocketConsumer):
    
    # ------------------------------------------------------------------
    # 1. CONNECT: การเชื่อมต่อ
    # ------------------------------------------------------------------
    async def connect(self):
        print("🔵 Attempting to connect...")
        try:
            self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
            self.room_group_name = f'restaurant_{self.restaurant_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            print(f"✅ Client Connected to Group: {self.room_group_name}")

        except Exception as e:
            print("❌ Error in connect:", e)
            await self.close()

    # ------------------------------------------------------------------
    # 2. DISCONNECT: ตัดการเชื่อมต่อ
    # ------------------------------------------------------------------
    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"🔴 Client Disconnected from {self.room_group_name}")
        except:
            pass

    # ------------------------------------------------------------------
    # 3. RECEIVE: รับข้อความจาก JS (Cashier) -> ส่งให้ Group
    # ------------------------------------------------------------------
    async def receive(self, text_data):
        print(f"📩 Received Message from Client: {text_data}") # <--- ดู Log ตรงนี้
        
        try:
            data = json.loads(text_data)
            command = data.get('command')

            # กรณี 1: สั่งโชว์หน้าจ่ายเงิน
            if command == 'show_customer_payment':
                print(f"📢 Broadcasting 'show_customer_payment' to group {self.room_group_name}")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'show_customer_payment', # ชื่อเมธอดที่จะทำงาน (ข้อ 4.1)
                        'items': data.get('items', []),
                        'total': data.get('total', '0.00')
                    }
                )

            # กรณี 2: สั่งปิดหน้าจอ
            elif command == 'hide_customer_payment':
                print(f"📢 Broadcasting 'hide_customer_payment' to group {self.room_group_name}")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'hide_customer_payment' # ชื่อเมธอดที่จะทำงาน (ข้อ 4.2)
                    }
                )

        except Exception as e:
            print("❌ Error processing message:", e)
            traceback.print_exc()

    # ------------------------------------------------------------------
    # 4. HANDLERS: รับคำสั่งจาก Group -> ส่งกลับไปที่ JS (Customer Display)
    # ------------------------------------------------------------------
    
    # 4.1 Handler สำหรับแสดงยอดเงิน (ต้องชื่อตรงกับ 'type' ด้านบน)
    async def show_customer_payment(self, event):
        # ส่ง JSON ไปหา Browser (Customer Display)
        await self.send(text_data=json.dumps({
            'type': 'show_customer_payment',
            'items': event['items'],
            'total': event['total']
        }))

    # 4.2 Handler สำหรับปิดหน้าจอ
    async def hide_customer_payment(self, event):
        await self.send(text_data=json.dumps({
            'type': 'hide_customer_payment'
        }))
        
    # 4.3 (แถม) Handler เดิมสำหรับการแจ้งเตือน Order
    async def order_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_notification',
            'message': event['message'],
            'order': event.get('order')
        }))