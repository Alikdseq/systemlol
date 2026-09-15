from django.db import migrations, models


def encrypt_values(apps, schema_editor):
    from clients.crypto import encrypt_str

    ProfileChangeRequest = apps.get_model("loyalty", "ProfileChangeRequest")
    for row in ProfileChangeRequest.objects.all():
        changed = False
        for attr in ("old_value", "new_value"):
            val = getattr(row, attr) or ""
            if val and not str(val).startswith("gAAAAA"):
                setattr(row, attr, encrypt_str(val))
                changed = True
        if changed:
            row.save(update_fields=["old_value", "new_value"])


class Migration(migrations.Migration):

    dependencies = [
        ("loyalty", "0007_bonuslot_remaining_lte_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profilechangerequest",
            name="old_value",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="profilechangerequest",
            name="new_value",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(encrypt_values, migrations.RunPython.noop),
    ]
