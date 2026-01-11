from django import forms
from .models import Restaurant, Category, MenuItem, RestaurantPromoImage
from users.models import User
from django.forms import inlineformset_factory

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['image', 'payment_qr_image', 'name', 'phone', 'address', 'vat_percent', 'service_charge_percent']
        labels = {
            'name': 'ชื่อร้าน',
            'phone': 'เบอร์โทรศัพท์',
            'address': 'ที่อยู่ร้าน',
            'vat_percent': 'VAT (%)',
            'service_charge_percent': 'Service Charge (%)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # วนลูปทุก field เพื่อใส่ class ของ Tailwind ให้สวยงาม
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 text-gray-800 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            })
            # ปรับแต่งเพิ่มเติมเฉพาะ field ถ้าต้องการ
            if field_name == 'address':
                field.widget.attrs.update({'rows': 3})



# 2. สร้าง Formset สำหรับรูปสไลด์โชว์

PromoImageFormSet = inlineformset_factory(
    Restaurant, 
    RestaurantPromoImage, 
    fields=['image'], 
    
    # ⭐ จุดสำคัญ: ปรับ extra เป็น 10 เพื่อให้โชว์ช่องว่างรอไว้เลย
    extra=10,    
    max_num=10, 
    
    # ป้องกันไม่ให้สร้างเกิน 10 (ถ้ามีรูปเดิม 2 รูป + extra 10 = 12 Django จะตัดให้เหลือ 10 อัตโนมัติ)
    validate_max=True,
    can_delete=True
)




class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'order']
        labels = {'name': 'ชื่อหมวดหมู่', 'order': 'ลำดับ (เลขน้อยขึ้นก่อน)'}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-3 text-gray-800 py-2 border border-gray-300 rounded-md'})

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'price', 'description', 'image', 'is_available']
        labels = {
            'category': 'หมวดหมู่',
            'name': 'ชื่อเมนู',
            'price': 'ราคา (บาท)',
            'is_available': 'เปิดขายอยู่'
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None) # รับค่า restaurant มากรอง category
        super().__init__(*args, **kwargs)
        
        # ใส่ Tailwind class
        for name, field in self.fields.items():
            if name != 'is_available': # checkbox ไม่ต้อง full width
                field.widget.attrs.update({'class': 'w-full px-3 text-gray-800 py-2 border border-gray-300 rounded-md'})
        
        # กรองให้เลือกได้เฉพาะ Category ของร้านตัวเองเท่านั้น! (สำคัญมาก)
        if restaurant:
            self.fields['category'].queryset = Category.objects.filter(restaurant=restaurant)



# setting form of retaurants
class RestaurantSettingsForm(forms.ModelForm):
    username = forms.CharField(
        label='ชื่อผู้ใช้ (Username)',
        max_length=150,
        required=True,
        help_text='ใช้สำหรับอ้างอิงในระบบ (ต้องไม่ซ้ำกับคนอื่น)'
    )
    class Meta:
        model = Restaurant
        fields = ['image', 'payment_qr_image', 'name', 'address', 'phone', 'vat_percent', 'service_charge_percent']
        labels = {
            'image': 'โลโก้ร้านค้า',
            'payment_qr_image': 'QR Code รับเงิน',
            'name': 'ชื่อร้านค้า',
            'address': 'ที่อยู่',
            'phone': 'เบอร์โทรศัพท์ติดต่อ',
            'vat_percent': 'ภาษีมูลค่าเพิ่ม (VAT %)',
            'service_charge_percent': 'ค่าบริการ (Service Charge %)'
        }
        
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            
            # Style ของ Logo
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            
            # ⭐ 2. เพิ่ม Style ให้ QR Code (หรือจะซ่อน class='hidden' ก็ได้ถ้าใช้ Label ครอบแล้ว)
            'payment_qr_image': forms.ClearableFileInput(attrs={
                'class': 'hidden' # ซ่อนไว้เพราะเรามี UI สวยๆ ใน HTML แล้ว
            })
        }

    # รับ user เข้ามาเพื่อดึงค่า username ปัจจุบันไปแสดง
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # จัด Style Tailwind ให้ field username
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 text-gray-400 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
        })
        
        # ใส่ค่าเดิมลงไปในช่อง
        if self.user:
            self.fields['username'].initial = self.user.username
        
        # จัด Style ให้ field อื่นๆ
        for name, field in self.fields.items():
            # เพิ่ม payment_qr_image เข้าไปในข้อยกเว้น เพราะเรา style แยกไว้ข้างบนแล้ว
            if name not in ['image', 'payment_qr_image']: 
                field.widget.attrs.update({
                    'class': 'w-full px-4 text-gray-800 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
                })

    # ฟังก์ชันตรวจสอบความถูกต้อง (Clean)
    def clean_username(self):
        username = self.cleaned_data['username']
        # เช็คว่าชื่อซ้ำคนอื่นไหม (ยกเว้นตัวเอง)
        if User.objects.filter(username=username).exclude(pk=self.instance.owner.pk).exists():
            raise forms.ValidationError("ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว กรุณาเปลี่ยนชื่อใหม่")
        return username