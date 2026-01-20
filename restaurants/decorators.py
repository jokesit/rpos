# restaurants/decorators.py (สร้างไฟล์ใหม่)
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from functools import wraps
from django.http import JsonResponse



def restaurant_active_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. ต้อง Login ก่อน
        if not request.user.is_authenticated:
            return redirect('login')

        # 2. ข้ามการเช็คถ้าเป็น Superuser (หรือจะให้เช็คด้วยก็ได้ แล้วแต่ design)
        if request.user.is_superuser:
             return view_func(request, *args, **kwargs)

        try:
            # 3. เช็คว่ามีร้านไหม และร้าน Active ไหม
            if hasattr(request.user, 'restaurant'):
                if not request.user.restaurant.is_active:
                    # ❌ ถ้าร้านถูกปิด -> ดีดไปหน้า Suspended
                    return redirect('restaurant_suspended')
            else:
                # ถ้าไม่มีร้าน ให้ไปหน้าสร้างร้าน (ตาม Logic เดิม)
                return redirect('create_restaurant')
                
        except ObjectDoesNotExist:
            return redirect('create_restaurant')

        # ✅ ถ้าร้าน Active -> ให้ทำงานต่อได้
        return view_func(request, *args, **kwargs)

    return _wrapped_view




# ⭐ สร้างอันใหม่ สำหรับ API โดยเฉพาะ
def api_restaurant_active_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. เช็คว่า Login หรือยัง
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized', 'success': False}, status=401)
        
        # 2. เช็ค Superuser (ผ่านตลอด)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            # 3. เช็คสถานะร้าน
            if hasattr(request.user, 'restaurant'):
                if not request.user.restaurant.is_active:
                    # ❌ ถ้าร้านถูกแบน Return JSON 403 Forbidden
                    return JsonResponse({
                        'error': 'Restaurant is suspended. Please contact support.',
                        'success': False
                    }, status=403)
            else:
                 return JsonResponse({'error': 'Restaurant not found', 'success': False}, status=404)
                 
        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

        # ✅ ผ่าน
        return view_func(request, *args, **kwargs)

    return _wrapped_view