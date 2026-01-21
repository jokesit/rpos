from django.urls import path
from . import api

urlpatterns = [
    path('api/create/', api.create_order_api, name='api_create_order'),
    path('api/update-status/', api.update_order_status, name='update_order_status'),
    # ดึงรายการทั้งหมดที่โต๊ะนั้นสั่ง
    path('api/history/', api.get_table_order_history, name='get_table_order_history'),
]