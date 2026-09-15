from datetime import date

from django.db import connection
from django.test import TestCase

from clients.models import Client
from loyalty.engine import process_birthdays_for_today
from loyalty.models import ProgramSettings
from loyalty.timeutils import moscow_today


class PiiEncryptionTests(TestCase):
    def setUp(self):
        ProgramSettings.get_solo()
        self.client_obj = Client.objects.create(
            telegram_id=89001,
            full_name="Секретный Клиент",
            phone="+79001230001",
            email="secret@example.com",
            birth_date=date(1990, moscow_today().month, moscow_today().day),
        )

    def test_db_does_not_store_plaintext_phone_email_name(self):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT full_name, phone, email, birth_date FROM clients_client WHERE telegram_id = %s",
                [89001],
            )
            name, phone, email, birth = cur.fetchone()
        self.assertTrue(str(name).startswith("gAAAAA"), name)
        self.assertTrue(str(phone).startswith("gAAAAA"), phone)
        self.assertTrue(str(email).startswith("gAAAAA"), email)
        self.assertTrue(str(birth).startswith("gAAAAA"), birth)
        self.assertNotIn("79001230001", str(phone))
        self.assertNotIn("secret@example.com", str(email))
        self.assertNotIn("Секретный", str(name))

    def test_orm_returns_plaintext(self):
        c = Client.objects.get(telegram_id=89001)
        self.assertEqual(c.phone, "+79001230001")
        self.assertEqual(c.email, "secret@example.com")
        self.assertEqual(c.full_name, "Секретный Клиент")

    def test_lookup_by_phone_hash(self):
        found = Client.objects.by_phone("+79001230001").first()
        self.assertIsNotNone(found)
        self.assertEqual(found.id, self.client_obj.id)

    def test_birthday_uses_birth_md(self):
        granted = process_birthdays_for_today()
        ids = {g["client_id"] for g in granted}
        self.assertIn(str(self.client_obj.id), ids)
