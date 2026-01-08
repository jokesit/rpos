# เพื่อตรวจสอบทุก Request ว่า User คนนี้ได้รับอนุมัติหรือยัง ถ้ายัง ให้ถีบไปหน้า pending-approval ทันที

from django.shortcuts import redirect
from django.urls import reverse

class ApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. ถ้าไม่ได้ Login ก็ปล่อยผ่าน (ให้ไปหน้า Login/Register ได้)
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 2. ถ้าเป็น Superuser ให้ผ่านตลอด
        if request.user.is_superuser:
            return self.get_response(request)
        
        # เพิ่มเงื่อนไข: ถ้าเป็น URL ของ django_browser_reload ให้ปล่อยผ่านเลย
        if request.path.startswith('/__reload__/'):
             return self.get_response(request)

        # 3. เช็คสถานะอนุมัติ
        if request.user.approval_status != 'APPROVED':
            # รายชื่อ URL ที่ยอมให้เข้าได้แม้ยังไม่อนุมัติ (เช่น หน้า Logout, หน้า Pending เอง)
            allowed_paths = [
                reverse('approval_pending'),
                reverse('account_logout'),
                '/admin/', # (เผื่อไว้)
            ]
            
            # ถ้า path ที่เข้า ไม่ใช่อันที่ยกเว้น -> บังคับ redirect ไปหน้า pending
            if request.path not in allowed_paths:
                return redirect('approval_pending')

        return self.get_response(request)