# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    
    # 1. หน้า List: ให้โชว์คอลัมน์อะไรบ้าง (เพิ่ม approval_status เข้าไปดูง่ายๆ)
    list_display = ['email', 'username', 'approval_status', 'is_shop_owner', 'is_staff', 'is_active']
    
    # 2. หน้า Edit: เพิ่ม Field ใหม่เข้าไปในฟอร์มแก้ไข
    # เราใช้ UserAdmin.fieldsets เดิม แล้วบวก Field ของเราเข้าไปต่อท้าย
    fieldsets = UserAdmin.fieldsets + (
        ('RPOS Additional Info', { # ตั้งชื่อ Section ใหม่
            'fields': ('approval_status', 'is_shop_owner', 'phone_number'),
        }),
    )
    
    # 3. หน้า Add User: เพิ่ม Field ตอนสร้าง User ใหม่ด้วย (ถ้าต้องการ)
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('email', 'approval_status', 'is_shop_owner', 'phone_number'),
        }),
    )

# Register Model กับ Admin
admin.site.register(User, CustomUserAdmin)