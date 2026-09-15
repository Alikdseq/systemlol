from django.db import migrations, models


def encrypt_client_rows(apps, schema_editor):
    from datetime import date as date_cls

    from clients.crypto import blind_index, encrypt_date, encrypt_str

    Client = apps.get_model("clients", "Client")
    for c in Client.objects.all():
        phone = c.phone or ""
        email = c.email or ""
        name = c.full_name or ""
        bd = c.birth_date
        if isinstance(bd, date_cls):
            bd_s = bd.isoformat()
        else:
            bd_s = str(bd or "")[:10]
        if phone and not str(phone).startswith("gAAAAA"):
            c.phone_hash = blind_index(phone)
            c.phone = encrypt_str(phone)
        if email and not str(email).startswith("gAAAAA"):
            c.email_hash = blind_index(str(email).strip().lower())
            c.email = encrypt_str(email)
        if name and not str(name).startswith("gAAAAA"):
            c.full_name = encrypt_str(name)
        if bd_s and not str(c.birth_date).startswith("gAAAAA"):
            try:
                parsed = date_cls.fromisoformat(bd_s)
            except ValueError:
                parsed = None
            if parsed:
                c.birth_md = f"{parsed.month:02d}{parsed.day:02d}"
                c.birth_date = encrypt_date(parsed)
        c.save()


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="client",
            name="phone",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="client",
            name="full_name",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="client",
            name="email",
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name="client",
            name="phone_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="client",
            name="email_hash",
            field=models.CharField(blank=True, default="", max_length=64, db_index=True),
        ),
        migrations.AddField(
            model_name="client",
            name="birth_md",
            field=models.CharField(blank=True, default="", max_length=4, db_index=True),
        ),
        migrations.AddField(
            model_name="client",
            name="birth_date_iso",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.RunSQL(
            sql="UPDATE clients_client SET birth_date_iso = birth_date::text WHERE birth_date IS NOT NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(model_name="client", name="birth_date"),
        migrations.RenameField(model_name="client", old_name="birth_date_iso", new_name="birth_date"),
        migrations.AlterField(
            model_name="client",
            name="birth_date",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(encrypt_client_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="client",
            name="phone_hash",
            field=models.CharField(db_index=True, max_length=64, unique=True),
        ),
    ]
