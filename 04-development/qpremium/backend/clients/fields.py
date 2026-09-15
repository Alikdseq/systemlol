from datetime import date

from django.db import models

from clients.crypto import decrypt_date, decrypt_str, encrypt_date, encrypt_str


class EncryptedTextField(models.TextField):
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "clients.fields.EncryptedTextField", args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return ""
        try:
            return decrypt_str(value)
        except ValueError:
            return "" if str(value).startswith("gAAAAA") else str(value)

    def to_python(self, value):
        if value is None:
            return ""
        return value

    def get_prep_value(self, value):
        if value is None or value == "":
            return ""
        return encrypt_str(str(value))


class EncryptedDateField(models.TextField):
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "clients.fields.EncryptedDateField", args, kwargs

    def from_db_value(self, value, expression, connection):
        if not value:
            return None
        try:
            return decrypt_date(value)
        except (ValueError, TypeError):
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                return None

    def to_python(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str) and not value.startswith("gAAAAA"):
            return date.fromisoformat(value[:10])
        return decrypt_date(value)

    def get_prep_value(self, value):
        if value is None or value == "":
            return ""
        return encrypt_date(value)
