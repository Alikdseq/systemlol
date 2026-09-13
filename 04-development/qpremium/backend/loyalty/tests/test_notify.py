from django.test import SimpleTestCase

from loyalty.notify import (
    msg_accrual_confirmed,
    msg_accrual_rejected,
    msg_birthday,
    msg_expiry_warning,
    msg_redemption,
)


class NotifyTextTests(SimpleTestCase):
    def test_accrual_confirmed(self):
        t = msg_accrual_confirmed(points=50, balance_total=150)
        self.assertIn("+50", t)
        self.assertIn("150", t)

    def test_accrual_rejected(self):
        t = msg_accrual_rejected(points=20, reason="ошибка")
        self.assertIn("20", t)
        self.assertIn("ошибка", t)

    def test_redemption(self):
        t = msg_redemption(points=30, balance_total=70)
        self.assertIn("30", t)
        self.assertIn("70", t)

    def test_birthday_template_points(self):
        t = msg_birthday(template="С ДР! +{points} баллов", points=1000)
        self.assertIn("1000", t)

    def test_expiry_warning_placeholders(self):
        t = msg_expiry_warning(
            template="Скоро сгорят {points} б. (до {date}), за {days} дн.",
            points=120,
            days=7,
            date_str="20.09.2026",
        )
        self.assertIn("120", t)
        self.assertIn("7", t)
        self.assertIn("20.09.2026", t)
