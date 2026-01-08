from django.urls import path
from . import api

urlpatterns = [
    path('api/create/', api.create_order_api, name='api_create_order'),
    path('api/update-status/', api.update_order_status, name='api_update_status'),
]