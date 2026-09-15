from django.db import migrations, models


def encrypt_names(apps, schema_editor):
    from clients.crypto import encrypt_str

    AdminUser = apps.get_model("stores", "AdminUser")
    for a in AdminUser.objects.all():
        name = a.display_name or ""
        if name and not str(name).startswith("gAAAAA"):
            a.display_name = encrypt_str(name)
            a.save(update_fields=["display_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="adminuser",
            name="display_name",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(encrypt_names, migrations.RunPython.noop),
    ]
