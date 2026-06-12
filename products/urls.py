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



    path("manufacturers/",                        views.manufacturer_list,     name="manufacturer_list"),
    path("manufacturers/<int:mfr_id>/",           views.manufacturer_products, name="manufacturer_products"),
    path("manufacturers/<int:mfr_id>/request/<int:product_id>/", views.request_product, name="request_product"),
    path("inbox/",                                views.request_inbox,         name="request_inbox"),
    path("inbox/<int:req_id>/accept/",            views.accept_request,        name="accept_request"),
    path("inbox/<int:req_id>/deny/",              views.deny_request,          name="deny_request"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("distributor/", views.distributor_home, name="distributor_home"),
]