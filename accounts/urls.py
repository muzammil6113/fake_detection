from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.role_home, name='role_home'),
    path('home/', views.home, name='home'),

    # Role-specific register
    path('register/manufacturer/', views.register_manufacturer, name='register_manufacturer'),
    path('register/distributor/', views.register_distributor, name='register_distributor'),
    path('register/customer/', views.register_customer, name='register_customer'),

    # Shared login/logout
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Role homes
    path('manufacturer/', views.manufacturer_home, name='manufacturer_home'),
    path('distributor/', views.distributor_home, name='distributor_home'),
    path('customer/', views.customer_home, name='customer_home'),
]