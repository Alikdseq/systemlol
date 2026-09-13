# Generated manually for promotions, profile changes, bot welcome

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0001_initial"),
        ("loyalty", "0003_broadcast_delivery"),
    ]

    operations = [
        migrations.AddField(
            model_name="programsettings",
            name="bot_welcome_text",
            field=models.TextField(
                blank=True,
                default="Добро пожаловать в Q Premium — программу лояльности магазинов одежды.",
            ),
        ),
        migrations.AddField(
            model_name="programsettings",
            name="bot_welcome_photo",
            field=models.ImageField(blank=True, null=True, upload_to="bot_welcome/"),
        ),
        migrations.CreateModel(
            name="Promotion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("conditions_text", models.TextField(blank=True, default="")),
                ("body_text", models.TextField(blank=True, default="")),
                (
                    "unit",
                    models.CharField(
                        choices=[("percent", "%"), ("rub", "₽")],
                        default="percent",
                        max_length=20,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["sort_order", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProfileChangeRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("field", models.CharField(default="birth_date", max_length=50)),
                ("old_value", models.CharField(max_length=100)),
                ("new_value", models.CharField(max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "PENDING"),
                            ("APPROVED", "APPROVED"),
                            ("REJECTED", "REJECTED"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("decided_by_telegram_id", models.BigIntegerField(blank=True, null=True)),
                ("comment", models.TextField(blank=True, default="")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile_change_requests",
                        to="clients.client",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="profilechangerequest",
            index=models.Index(fields=["status", "-created_at"], name="loyalty_pro_status_7f2a1c_idx"),
        ),
    ]
