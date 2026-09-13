from django.db import models
from django.contrib.auth.models import User


class Store(models.Model):
    name = models.CharField("Магазин", max_length=120)
    code = models.SlugField("Код", unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"

    def __str__(self):
        return self.name


class StaffProfile(models.Model):
    ROLE_CASHIER = "cashier"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = (
        (ROLE_CASHIER, "Кассир"),
        (ROLE_ADMIN, "Админ"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Обязателен для кассира. Админ — все точки.",
    )

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_cashier(self):
        return self.role == self.ROLE_CASHIER

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Client(models.Model):
    phone = models.CharField("Телефон", max_length=11, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return self.phone


class Account(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="account")
    balance_bonus = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.phone}: {self.balance_bonus}"


class LoyaltyRule(models.Model):
    """Singleton pk=1. percent of check → bonuses (floor)."""

    percent = models.DecimalField("Процент начисления", max_digits=5, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Правило начисления"

    def __str__(self):
        return f"{self.percent}%"


class Operation(models.Model):
    ACCRUAL = "accrual"
    REDEEM = "redeem"
    ADJUST = "adjust"
    TYPE_CHOICES = (
        (ACCRUAL, "Начисление"),
        (REDEEM, "Списание"),
        (ADJUST, "Корректировка"),
    )

    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="operations")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True)
    staff = models.ForeignKey(User, on_delete=models.PROTECT)
    amount_bonus = models.IntegerField(help_text="Знак: + начисление/adjust+, − списание/adjust−")
    check_amount_rub = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True)
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Операция"
        verbose_name_plural = "Операции"
