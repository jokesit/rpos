# orders/models.py
from django.db import models

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'รอรับออเดอร์'),
        ('COOKING', 'กำลังปรุง'),
        ('SERVED', 'เสิร์ฟแล้ว'),
        ('COMPLETED', 'ทานเสร็จ/เช็คบิล'),
        ('CANCELLED', 'ยกเลิก'),
    ]

    # อ้างอิงข้าม App ใช้ string 'app_name.ModelName'
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey('restaurants.Table', on_delete=models.SET_NULL, null=True, related_name='orders')
    
    session_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False) 
    payment_method = models.CharField(max_length=20, default='CASH', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.PROTECT) # อ้างอิงเมนู
    
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    note = models.CharField(max_length=255, blank=True, verbose_name="หมายเหตุ")
    
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
        
    @property
    def total_cost(self):
        return self.price * self.quantity