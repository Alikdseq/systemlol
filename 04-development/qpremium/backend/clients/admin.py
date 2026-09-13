from django.contrib import admin

from clients.models import Client, ConsentRecord


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "telegram_id", "registered_at")
    search_fields = ("full_name", "phone", "email")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("client", "consent_type", "status", "accepted_at", "text_version")
    list_filter = ("consent_type", "status")
    readonly_fields = (
        "client",
        "consent_type",
        "status",
        "accepted_at",
        "text_version",
        "consent_text_hash",
        "telegram_id",
        "ip_address",
        "user_agent",
        "created_at",
    )
