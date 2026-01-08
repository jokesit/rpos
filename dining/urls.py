# dining/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # เช่น dining/my-coffee-shop/uuid-1234/
    path('<slug:shop_slug>/<uuid:table_uuid>/', views.dining_menu, name='dining_menu'),
]