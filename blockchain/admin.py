# from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import BlockRecord


@admin.register(BlockRecord)
class BlockRecordAdmin(admin.ModelAdmin):
    list_display    = ("index", "event_type", "product_unit_serial", "actor_username", "actor_role", "created_at")
    readonly_fields = ("index", "block_hash", "previous_hash", "nonce", "timestamp")
    list_filter     = ("event_type", "actor_role")
    search_fields   = ("product_unit_serial", "actor_username", "block_hash")
    ordering        = ("-index",)