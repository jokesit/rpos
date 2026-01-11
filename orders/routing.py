# orders/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # URL สำหรับ WebSocket: ws://localhost:8000/ws/orders/1/
    re_path(r'ws/orders/(?P<restaurant_id>\w+)/$', consumers.OrderConsumer.as_asgi()),
    
    re_path(r'ws/restaurant/(?P<restaurant_id>\w+)/$', consumers.OrderConsumer.as_asgi()),
]