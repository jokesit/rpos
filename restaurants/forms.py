from django import forms
from .models import Restaurant, Category, MenuItem

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'phone', 'address', 'vat_percent', 'service_charge_percent']
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
    class Meta:
        model = Restaurant
        fields = ['name', 'address', 'phone', 'vat_percent', 'service_charge_percent']
        labels = {
            'name': 'ชื่อร้านค้า',
            'address': 'ที่อยู่',
            'phone': 'เบอร์โทรศัพท์ติดต่อ',
            'vat_percent': 'ภาษีมูลค่าเพิ่ม (VAT %)',
            'service_charge_percent': 'ค่าบริการ (Service Charge %)'
        }
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # จัด Style ให้สวยงามด้วย Tailwind
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition'
            })