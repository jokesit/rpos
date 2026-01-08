from django.urls import path
from . import views

urlpatterns = [
    # เข้ามาที่ /restaurant/ จะเจอ Dashboard เป็นหน้าแรก
    path('', views.dashboard, name='dashboard'),
    
    # เข้ามาที่ /restaurant/create/ เพื่อสร้างร้าน
    path('create/', views.create_restaurant, name='create_restaurant'),
    # จัดการโต๊ะ
    path('tables/', views.table_list, name='table_list'),
    path('tables/delete/<int:table_id>/', views.delete_table, name='delete_table'),
    # Menu Management
    path('menu/', views.menu_manage, name='menu_manage'),
    path('menu/category/add/', views.add_category, name='add_category'),
    path('menu/item/add/', views.add_menu_item, name='add_menu_item'),
    # Menu Items Edit/Delete
    path('menu/item/edit/<int:item_id>/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/item/delete/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    
    # Category Edit/Delete 
    path('menu/category/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('menu/category/delete/<int:category_id>/', views.delete_category, name='delete_category'),

    # kitchen
    path('kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    # for cashier
    path('cashier/', views.cashier_dashboard, name='cashier_dashboard'),
    
    path('cashier/<int:table_id>/bill/', views.table_bill_detail, name='table_bill_detail'),
    path('cashier/<int:table_id>/pay/', views.close_bill, name='close_bill'),

    path('report/', views.report_sales, name='report_sales'),
]