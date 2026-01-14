from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('super-admin/', admin.site.urls),
    # URL ของ Allauth (Login, Logout, Signup, Password Reset)
    path('accounts/', include('allauth.urls')),

    path('users/', include('users.urls')),
    # ทุกอย่างที่เกี่ยวกับร้านค้า ให้ขึ้นต้นด้วย /restaurant/
    path('restaurants/', include('restaurants.urls')),
    path('dining/', include('dining.urls')),
    path('orders/', include('orders.urls')),



    # for auto reload
    path("__reload__/", include("django_browser_reload.urls")),


]


# เพิ่มต่อท้าย urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)