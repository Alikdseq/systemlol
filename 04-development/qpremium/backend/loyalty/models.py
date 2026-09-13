import uuid

from django.db import models

from clients.models import Client
from stores.models import Store


class ProgramSettings(models.Model):
    """Singleton id=1."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    accrual_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    max_redeem_percent = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    min_purchase_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000)
    earned_ttl_days = models.PositiveIntegerField(default=90)
    gift_ttl_days = models.PositiveIntegerField(default=30)
    registration_gift_points = models.PositiveIntegerField(default=500)
    birthday_gift_points = models.PositiveIntegerField(default=1000)
    birthday_message_template = models.TextField(
        default="Поздравляем с днём рождения! Вам начислены подарочные баллы."
    )
    points_expiry_warning_days = models.PositiveIntegerField(
        default=7,
        help_text="За сколько дней до сгорания предупреждать клиента",
    )
    points_expiry_warning_template = models.TextField(
        blank=True,
        default=(
            "Здравствуйте! Напоминаем: в ближайшие дни могут сгореть {points} баллов "
            "(до {date}). Будем рады видеть вас в магазинах Q Premium — успейте ими воспользоваться."
        ),
        help_text="Плейсхолдеры: {points}, {days}, {date}",
    )
    rules_text = models.TextField(blank=True, default="")
    promotions_text = models.TextField(blank=True, default="")  # legacy, read-only fallback
    bot_welcome_text = models.TextField(
        blank=True,
        default="Добро пожаловать в Q Premium — программу лояльности магазинов одежды.",
    )
    bot_welcome_photo = models.ImageField(upload_to="bot_welcome/", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_telegram_id = models.BigIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class Operation(models.Model):
    class Type(models.TextChoices):
        BONUS_ACCRUAL = "BONUS_ACCRUAL"
        BONUS_REDEMPTION = "BONUS_REDEMPTION"
        GIFT_ACCRUAL = "GIFT_ACCRUAL"
        BONUS_EXPIRATION = "BONUS_EXPIRATION"
        MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
        REGISTRATION_GIFT = "REGISTRATION_GIFT"
        BIRTHDAY_GIFT = "BIRTHDAY_GIFT"

    class Status(models.TextChoices):
        PENDING = "PENDING"
        CONFIRMED = "CONFIRMED"
        REJECTED = "REJECTED"
        CANCELLED = "CANCELLED"

    class PointType(models.TextChoices):
        EARNED = "earned"
        GIFT = "gift"
        MIXED = "mixed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="operations")
    type = models.CharField(max_length=40, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    points = models.IntegerField()
    point_type = models.CharField(max_length=20, choices=PointType.choices, null=True, blank=True)
    store = models.ForeignKey(Store, null=True, blank=True, on_delete=models.SET_NULL)
    store_name_snapshot = models.CharField(max_length=200, blank=True, default="")
    store_address_snapshot = models.CharField(max_length=500, blank=True, default="")
    operator_telegram_id = models.BigIntegerField(null=True, blank=True)
    operator_name_snapshot = models.CharField(max_length=200, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    override_reason = models.TextField(blank=True, default="")
    idempotency_key = models.CharField(max_length=64, null=True, blank=True, unique=True)
    request_hash = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)


class BonusLot(models.Model):
    class PointType(models.TextChoices):
        EARNED = "earned"
        GIFT = "gift"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="lots")
    point_type = models.CharField(max_length=20, choices=PointType.choices)
    initial_points = models.PositiveIntegerField()
    remaining_points = models.PositiveIntegerField()
    source_operation = models.ForeignKey(
        Operation, null=True, blank=True, on_delete=models.SET_NULL, related_name="lots"
    )
    accrued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    is_expired = models.BooleanField(default=False)
    expiry_warning_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "expires_at", "accrued_at", "id"]),
            models.Index(fields=["is_expired", "expiry_warning_sent_at", "expires_at"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(remaining_points__gte=0), name="bonuslot_remaining_gte_0"),
            models.CheckConstraint(
                condition=models.Q(remaining_points__lte=models.F("initial_points")),
                name="bonuslot_remaining_lte_initial",
            ),
        ]


class OperationLotAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name="allocations")
    lot = models.ForeignKey(BonusLot, on_delete=models.CASCADE, related_name="allocations")
    points = models.PositiveIntegerField()


class BirthdayGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="birthday_grants")
    year = models.PositiveIntegerField()
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("client", "year"),)


class Broadcast(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField()
    audience_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    created_by_telegram_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)


class BroadcastDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "pending"
        SENT = "sent", "sent"
        FAILED = "failed", "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    broadcast = models.ForeignKey(Broadcast, on_delete=models.CASCADE, related_name="deliveries")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="broadcast_deliveries")
    telegram_id = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error = models.CharField(max_length=500, blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("broadcast", "client"),)
        indexes = [
            models.Index(fields=["broadcast", "status"]),
        ]


class Promotion(models.Model):
    class Unit(models.TextChoices):
        PERCENT = "percent", "%"
        RUB = "rub", "₽"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    conditions_text = models.TextField(blank=True, default="")
    body_text = models.TextField(blank=True, default="")
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.PERCENT)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]


class ProfileChangeRequest(models.Model):
    """Смена ДР клиентом — только после подтверждения ADMIN (антифрод)."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "PENDING"
        APPROVED = "APPROVED", "APPROVED"
        REJECTED = "REJECTED", "REJECTED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="profile_change_requests")
    field = models.CharField(max_length=50, default="birth_date")
    old_value = models.CharField(max_length=100)
    new_value = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by_telegram_id = models.BigIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["status", "-created_at"])]

