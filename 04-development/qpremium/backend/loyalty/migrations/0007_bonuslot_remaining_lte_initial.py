from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("loyalty", "0006_rename_indexes"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="bonuslot",
            constraint=models.CheckConstraint(
                condition=models.Q(remaining_points__gte=0),
                name="bonuslot_remaining_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="bonuslot",
            constraint=models.CheckConstraint(
                condition=models.Q(("remaining_points__lte", models.F("initial_points"))),
                name="bonuslot_remaining_lte_initial",
            ),
        ),
    ]
