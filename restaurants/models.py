from django.db import models
from django.conf import settings # เพื่ออ้างอิง User model
from django.utils.text import slugify
import uuid
import segno
from utils import compress_image

class Restaurant(models.Model):
    # เชื่อมกับ User: ถ้า User ถูกลบ ร้านหายไปด้วย (CASCADE)
    # ใช้ OneToOneField เพราะโจทย์คือ 1 User มี 1 ร้าน (ถ้าอนาคตเปลี่ยนเป็น ForeignKey ก็ได้)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restaurant')
    
    name = models.CharField(max_length=255, verbose_name="ชื่อร้าน")
    
    # field รูปภาพร้านค้า
    image = models.ImageField(upload_to='restaurant_images/', blank=True, null=True, verbose_name="รูปร้านค้า/โลโก้")
    
    # เพิ่มรูป Payment QR Code
    payment_qr_image = models.ImageField(upload_to='payment_qrs/', blank=True, null=True, verbose_name="QR Code รับเงิน (ธนาคาร)")

    # Slug เอาไว้ทำ URL สวยๆ เช่น rpos.com/shop/my-coffee-shop/
    slug = models.SlugField(unique=True, blank=True, null=True) 
    
    address = models.TextField(blank=True, verbose_name="ที่อยู่ร้าน")
    phone = models.CharField(max_length=20, blank=True, verbose_name="เบอร์โทรศัพท์ร้าน")
    
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="VAT %")
    service_charge_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Service Charge %")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    # for create slug
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or str(uuid.uuid4())[:8]
            slug = base_slug
            counter = 1
            # check duplicate
            while Restaurant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug 

        if self.image:
            try:
                # เรียกใช้ฟังก์ชันจาก utils.py (ขนาด 800x800)
                new_image = compress_image(self.image, max_size=(800, 800))
                if new_image:
                    self.image = new_image
            except Exception as e:
                # กรณี Error (เช่น ไฟล์ไม่ใช่รูป) ให้ข้ามไป ไม่ต้องย่อ
                print(f"Image compression failed: {e}")

        # เพิ่ม Logic ย่อรูป Payment QR
        if self.payment_qr_image:
            try:
                new_image = compress_image(self.payment_qr_image, max_size=(500, 500))
                if new_image:
                    self.payment_qr_image = new_image
            except Exception:
                # กรณี Error (เช่น ไฟล์ไม่ใช่รูป) ให้ข้ามไป ไม่ต้องย่อ
                print(f"Image compression failed: {e}")
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    


class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50, verbose_name="ชื่อโต๊ะ") # เช่น T1, A1, VIP
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) # รหัสลับสำหรับ QR Code
    
    # เก็บรูป QR Code (เผื่ออยาก cache ไว้ แต่จริงๆ Gen สดก็ได้)
    # ในที่นี้เราจะ Gen สดตอนเรียกใช้เพื่อประหยัดพื้นที่ DB
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name'] # เรียงตามชื่อโต๊ะ

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

    def get_order_url(self):
        # พยายามดึง Domain จาก settings ถ้าไม่มีใช้ localhost
        domain = getattr(settings, 'DOMAIN_URL', 'http://127.0.0.1:8000')
        # ลบ slash ท้าย domain ออกถ้ามี เพื่อความชัวร์
        domain = domain.rstrip('/')
        return f"{domain}/dining/{self.restaurant.slug}/{self.uuid}/"

    def get_qr_image(self):
        # สร้าง QR Code แบบ Base64 เพื่อเอาไปแสดงใน HTML ได้เลย โดยไม่ต้องบันทึกไฟล์
        qr = segno.make_qr(self.get_order_url())
        
        # คืนค่าเป็น Data URI scheme (ใช้ใส่ใน tag <img src="..."> ได้เลย)
        return qr.png_data_uri(scale=10)
    
    # for kill link
    def refresh_uuid(self):
        """เปลี่ยนรหัส UUID ใหม่ เพื่อให้ Link เก่าใช้งานไม่ได้"""
        self.uuid = uuid.uuid4()
        self.save()
    


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    order = models.PositiveIntegerField(default=0, verbose_name="ลำดับการแสดงผล")

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200, verbose_name="ชื่ออาหาร")
    description = models.TextField(blank=True, verbose_name="รายละเอียด")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True, verbose_name="รูปภาพ")
    is_available = models.BooleanField(default=True, verbose_name="มีจำหน่าย")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    # ⭐ เพิ่ม method save เพื่อย่อรูปอาหาร
    def save(self, *args, **kwargs):
        if self.image:
            try:
                # รูปอาหารเอาขนาด 600x600 พอดีจอมือถือ
                new_image = compress_image(self.image, max_size=(600, 600))
                if new_image:
                    self.image = new_image
            except Exception as e:
                print(f"Menu image compression failed: {e}")
                
        super().save(*args, **kwargs)



# สร้าง Model สำหรับรูปสไลด์โชว์ (Promotion Images)
class RestaurantPromoImage(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='promo_images')
    image = models.ImageField(upload_to='promo_images/', verbose_name="รูปโปรโมชั่น/เมนูแนะนำ")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:
            try:
                # รูปสไลด์โชว์ควรชัดหน่อย เอาสัก 1280x720 หรือ 1920x1080
                new_image = compress_image(self.image, max_size=(1280, 720))
                if new_image:
                    self.image = new_image
            except Exception:
                pass
        super().save(*args, **kwargs)