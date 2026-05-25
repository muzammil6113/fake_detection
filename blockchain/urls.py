from django.urls import path
from . import views

app_name = 'blockchain'

urlpatterns = [
    path('scan/',         views.scan_page,   name='scan'),
    path('verify-hash/',  views.verify_hash, name='verify_hash'),
]