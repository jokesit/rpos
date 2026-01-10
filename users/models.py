# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # สถานะการอนุมัติ
    STATUS_CHOICES = [
        ('PENDING', 'รออนุมัติ'),
        ('APPROVED', 'อนุมัติแล้ว'),
        ('REJECTED', 'ไม่อนุมัติ'),
        ('SUSPENDED', 'ระงับการใช้งาน'),
    ]
    email = models.EmailField(unique=True, verbose_name='Email Address')
    
    # User Types (เผื่ออนาคตอยากแยก Role ชัดเจนในระดับ Model)
    is_shop_owner = models.BooleanField(default=False, verbose_name="เป็นเจ้าของร้าน")
    
    approval_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name="สถานะการอนุมัติ"
    )
    
    # เพิ่ม field อื่นๆ ได้ที่นี่ เช่น เบอร์โทร
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.email