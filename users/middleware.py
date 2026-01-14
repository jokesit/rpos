# เพื่อตรวจสอบทุก Request ว่า User คนนี้ได้รับอนุมัติหรือยัง ถ้ายัง ให้ถีบไปหน้า pending-approval ทันที

from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.conf import settings
import environ


# อ่านค่า env (เผื่อกรณีไม่ได้อ่านผ่าน settings)
env = environ.Env()


# --- 1. Middleware สำหรับจำกัด IP เข้าหน้า Admin ---
class AdminIPRestrictMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # เช็คว่ากำลังเข้าหน้า Admin หรือไม่
        if request.path.startswith('/super-admin/'):
            
            # เช็คว่าเปิดใช้งานระบบป้องกันไหม (ดึงจาก settings)
            restrict_enabled = getattr(settings, 'ADMIN_IP_RESTRICTION', False)
            
            if restrict_enabled:
                # ดึง IP ของผู้ใช้
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                # ดึงรายการ IP ที่อนุญาต
                allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', [])

                if ip not in allowed_ips:
                    return HttpResponseForbidden(f"⛔ Access Denied: Your IP ({ip}) is not allowed.")

        return self.get_response(request)
    



# --- 2. Middleware เดิมของคุณ (ตรวจสอบสถานะอนุมัติ) ---
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
    


# use when web maintenance
class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. ตรวจสอบว่าเปิดโหมดซ่อมบำรุงหรือไม่? (ค่า Default คือ False)
        maintenance_mode = getattr(settings, 'MAINTENANCE_MODE', False)

        if maintenance_mode:
            # 2. ข้อยกเว้น: ยอมให้ผ่านถ้าเป็น...
            # - เข้าหน้า Admin
            # - เป็น Superuser (เพื่อให้เจ้าของระบบเทสได้)
            # - ไฟล์ Static/Media (เพื่อให้หน้าเว็บแสดงผลสวยงาม)
            
            is_admin_url = request.path.startswith('/super-admin/')
            is_static_url = request.path.startswith(settings.STATIC_URL)
            is_media_url = request.path.startswith(settings.MEDIA_URL)
            
            # ต้องตรวจสอบ request.user ก่อนเรียกใช้ .is_superuser 
            # (ป้องกัน Error กรณี Middleware รันก่อน Authentication)
            is_superuser = request.user.is_authenticated and request.user.is_superuser

            if not (is_admin_url or is_static_url or is_media_url or is_superuser):
                # ถ้าไม่ใช่ข้อยกเว้น -> ส่งหน้า 503 กลับไปทันที
                return render(request, '503.html', status=503)

        return self.get_response(request)