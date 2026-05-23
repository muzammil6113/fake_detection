from django.contrib import admin
from .models import Category, ProductModel, ProductUnit, TransferHistory, ScanLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display  = ("model_code", "name", "brand", "manufacturer", "unit_count", "created_at")
    list_filter   = ("brand", "category")
    search_fields = ("name", "brand", "model_code")

@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display    = ("serial_number", "model", "status", "current_owner", "created_at")
    list_filter     = ("status",)
    search_fields   = ("serial_number", "product_hash")
    readonly_fields = ("product_hash", "blockchain_block_hash")

@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):
    list_display = ("unit", "from_user", "to_user", "transferred_at")

@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display  = ("product_hash_scanned", "result", "scanner_ip", "geo_city", "geo_country", "scanned_at")
    list_filter   = ("result",)
    search_fields = ("product_hash_scanned", "scanner_ip")