from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from loyalty.models import Client, LoyaltyRule, StaffProfile, Store
from loyalty.services import (
    DomainError,
    accrue,
    adjust,
    bonuses_from_check,
    create_client,
    lookup_client,
    normalize_phone,
    redeem,
)


class PhoneTests(TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_phone("8 (999) 123-45-67"), "79991234567")
        self.assertEqual(normalize_phone("9991234567"), "79991234567")
        with self.assertRaises(DomainError):
            normalize_phone("123")


class AccrualTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Магазин 1", code="s1")
        self.user = User.objects.create_user("cashier", password="x")
        StaffProfile.objects.create(user=self.user, role=StaffProfile.ROLE_CASHIER, store=self.store)
        LoyaltyRule.objects.create(pk=1, percent=Decimal("10.00"))
        self.client_obj = create_client("79991234567")

    def test_ten_percent_floor(self):
        self.assertEqual(bonuses_from_check(Decimal("1000.00"), Decimal("10")), 100)
        self.assertEqual(bonuses_from_check(Decimal("999.99"), Decimal("10")), 99)

    def test_accrue_and_idempotent(self):
        op1 = accrue(
            client=self.client_obj,
            store=self.store,
            staff=self.user,
            check_amount=Decimal("1000"),
            idempotency_key="k1",
        )
        op2 = accrue(
            client=self.client_obj,
            store=self.store,
            staff=self.user,
            check_amount=Decimal("1000"),
            idempotency_key="k1",
        )
        self.assertEqual(op1.id, op2.id)
        self.client_obj.account.refresh_from_db()
        self.assertEqual(self.client_obj.account.balance_bonus, 100)

    def test_redeem_and_insufficient(self):
        accrue(
            client=self.client_obj,
            store=self.store,
            staff=self.user,
            check_amount=Decimal("1000"),
            idempotency_key="a",
        )
        redeem(
            client=self.client_obj,
            store=self.store,
            staff=self.user,
            check_amount=Decimal("500"),
            bonus_to_redeem=50,
            idempotency_key="r1",
        )
        self.client_obj.account.refresh_from_db()
        self.assertEqual(self.client_obj.account.balance_bonus, 50)
        with self.assertRaises(DomainError) as ctx:
            redeem(
                client=self.client_obj,
                store=self.store,
                staff=self.user,
                check_amount=Decimal("500"),
                bonus_to_redeem=51,
                idempotency_key="r2",
            )
        self.assertEqual(ctx.exception.code, "insufficient")

    def test_redeem_cannot_exceed_check(self):
        accrue(
            client=self.client_obj,
            store=self.store,
            staff=self.user,
            check_amount=Decimal("10000"),
            idempotency_key="a2",
        )
        with self.assertRaises(DomainError) as ctx:
            redeem(
                client=self.client_obj,
                store=self.store,
                staff=self.user,
                check_amount=Decimal("10"),
                bonus_to_redeem=11,
                idempotency_key="r3",
            )
        self.assertEqual(ctx.exception.code, "redeem_gt_check")

    def test_lookup(self):
        found = lookup_client("8 999 123-45-67")
        self.assertEqual(found.id, self.client_obj.id)

    def test_adjust_needs_comment(self):
        with self.assertRaises(DomainError):
            adjust(client=self.client_obj, staff=self.user, delta=10, comment="  ")
        adjust(client=self.client_obj, staff=self.user, delta=10, comment="подарок")
        self.client_obj.account.refresh_from_db()
        self.assertEqual(self.client_obj.account.balance_bonus, 10)


class HttpFlowTests(TestCase):
    """QA: M1–M6, E1 через Django test client (не визуальный браузер)."""

    def setUp(self):
        self.store = Store.objects.create(name="Магазин 1", code="s1")
        Store.objects.create(name="Магазин 2", code="s2")
        LoyaltyRule.objects.create(pk=1, percent=Decimal("10.00"))
        self.cashier = User.objects.create_user("cashier1", password="devpass")
        StaffProfile.objects.create(
            user=self.cashier, role=StaffProfile.ROLE_CASHIER, store=self.store
        )
        self.admin = User.objects.create_user(
            "admin", password="devpass", is_staff=True, is_superuser=True
        )
        StaffProfile.objects.create(
            user=self.admin, role=StaffProfile.ROLE_ADMIN, store=None
        )

    def test_m2_create_then_m1_accrual(self):
        self.client.login(username="cashier1", password="devpass")
        r = self.client.post("/cashier/", {"phone": "89991112233"})
        self.assertContains(r, "В базе нет")
        r = self.client.post("/cashier/create/", {"phone": "89991112233"}, follow=True)
        self.assertEqual(r.status_code, 200)
        client = Client.objects.get(phone="79991112233")
        r = self.client.post(
            f"/cashier/client/{client.id}/",
            {
                "action": "accrual",
                "check_amount_rub": "1000",
                "idempotency_key": "qa-acc-1",
            },
            follow=True,
        )
        self.assertContains(r, "Начислено 100 бонусов")
        client.account.refresh_from_db()
        self.assertEqual(client.account.balance_bonus, 100)

    def test_m3_redeem_and_e1_insufficient(self):
        cl = create_client("79990001122")
        self.client.login(username="cashier1", password="devpass")
        self.client.post(
            f"/cashier/client/{cl.id}/",
            {"action": "accrual", "check_amount_rub": "1000", "idempotency_key": "qa-a"},
            follow=True,
        )
        r = self.client.post(
            f"/cashier/client/{cl.id}/",
            {
                "action": "redeem",
                "check_amount_rub": "500",
                "bonus_to_redeem": "50",
                "idempotency_key": "qa-r",
            },
            follow=True,
        )
        self.assertContains(r, "скидку 50 руб")
        r = self.client.post(
            f"/cashier/client/{cl.id}/",
            {
                "action": "redeem",
                "check_amount_rub": "500",
                "bonus_to_redeem": "51",
                "idempotency_key": "qa-r2",
            },
            follow=True,
        )
        self.assertContains(r, "Недостаточно бонусов")
        cl.account.refresh_from_db()
        self.assertEqual(cl.account.balance_bonus, 50)

    def test_cashier_forbidden_office(self):
        self.client.login(username="cashier1", password="devpass")
        r = self.client.get("/office/clients/")
        self.assertEqual(r.status_code, 403)

    def test_m5_m6_admin_history_adjust_rule(self):
        cl = create_client("79993334455")
        self.client.login(username="cashier1", password="devpass")
        self.client.post(
            f"/cashier/client/{cl.id}/",
            {"action": "accrual", "check_amount_rub": "2000", "idempotency_key": "qa-a2"},
            follow=True,
        )
        self.client.logout()
        self.client.login(username="admin", password="devpass")
        r = self.client.get(f"/office/clients/{cl.id}/")
        self.assertContains(r, "Начисление")
        r = self.client.post(
            f"/office/clients/{cl.id}/",
            {"action": "adjust", "delta": "5", "comment": "подарок QA"},
            follow=True,
        )
        self.assertContains(r, "Баланс изменён")
        r = self.client.post("/office/rule/", {"percent": "10"}, follow=True)
        self.assertContains(r, "Правило сохранено")

    def test_invalid_phone(self):
        self.client.login(username="cashier1", password="devpass")
        r = self.client.post("/cashier/", {"phone": "12"})
        self.assertContains(r, "Не похоже на российский мобильный")
