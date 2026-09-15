import uuid

from django.db import models

from clients.crypto import blind_index
from clients.fields import EncryptedDateField, EncryptedTextField


class ClientQuerySet(models.QuerySet):
    def by_phone(self, phone: str):
        return self.filter(phone_hash=blind_index(phone or ""))


class Client(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "active"
        BLOCKED = "blocked", "blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telegram_id = models.BigIntegerField(unique=True)
    full_name = EncryptedTextField()
    phone = EncryptedTextField()
    phone_hash = models.CharField(max_length=64, unique=True, db_index=True)
    email = EncryptedTextField()
    email_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)
    birth_date = EncryptedDateField()
    birth_md = models.CharField(max_length=4, db_index=True, help_text="MMDD for birthday job; not the year")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_operation_at = models.DateTimeField(null=True, blank=True)
    total_purchase_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_purchase_count = models.IntegerField(default=0)

    objects = ClientQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone_hash = blind_index(self.phone)
        if self.email:
            self.email_hash = blind_index(str(self.email).strip().lower())
        if self.birth_date:
            self.birth_md = f"{self.birth_date.month:02d}{self.birth_date.day:02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"client:{self.id}"


class ConsentRecord(models.Model):
    """Append-only proof for Роскомнадзор / audits."""

    class ConsentType(models.TextChoices):
        PROGRAM_RULES = "PROGRAM_RULES", "PROGRAM_RULES"
        PERSONAL_DATA = "PERSONAL_DATA", "PERSONAL_DATA"
        ADVERTISING = "ADVERTISING", "ADVERTISING"

    class Status(models.TextChoices):
        ACCEPTED = "accepted", "accepted"
        REVOKED = "revoked", "revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=50, choices=ConsentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    accepted_at = models.DateTimeField()
    text_version = models.CharField(max_length=50)
    consent_text_hash = models.CharField(max_length=64)
    telegram_id = models.BigIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "consent_type", "-created_at"]),
        ]
