from django.urls import path
from . import views


urlpatterns = [
    path('pending-approval/', views.approval_pending, name='approval_pending'),
]