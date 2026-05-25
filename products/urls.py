from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path("",                              views.home,                 name="home"),
    path("dashboard/",                   views.dashboard,            name="dashboard"),
    path("products/new/",                views.create_product_model, name="create_product_model"),
    path("products/<int:pk>/",           views.product_model_detail, name="product_model_detail"),
    path("products/<int:pk>/generate/",  views.generate_units,       name="generate_units"),
    path("units/<str:serial>/",          views.unit_detail,          name="unit_detail"),
    path("units/<str:serial>/transfer/", views.transfer_unit,        name="transfer_unit"),
    path("verify/<str:product_hash>/",   views.verify_unit,          name="verify_unit"),
    path("chain/",                       views.chain_status,         name="chain_status"),
    path("api/scan-stats/",              views.api_scan_stats,       name="api_scan_stats"),
]