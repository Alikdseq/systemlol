# Generated manually for expiry warning + operator name snapshot

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("loyalty", "0004_promotions_profile_welcome"),
    ]

    operations = [
        migrations.AddField(
            model_name="programsettings",
            name="points_expiry_warning_days",
            field=models.PositiveIntegerField(
                default=7,
                help_text="За сколько дней до сгорания предупреждать клиента",
            ),
        ),
        migrations.AddField(
            model_name="programsettings",
            name="points_expiry_warning_template",
            field=models.TextField(
                blank=True,
                default=(
                    "Здравствуйте! Напоминаем: в ближайшие дни могут сгореть {points} баллов "
                    "(до {date}). Будем рады видеть вас в магазинах Q Premium — успейте ими воспользоваться."
                ),
                help_text="Плейсхолдеры: {points}, {days}, {date}",
            ),
        ),
        migrations.AddField(
            model_name="operation",
            name="operator_name_snapshot",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="bonuslot",
            name="expiry_warning_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="bonuslot",
            index=models.Index(
                fields=["is_expired", "expiry_warning_sent_at", "expires_at"],
                name="loyalty_bon_is_expi_7c1a2b_idx",
            ),
        ),
    ]
