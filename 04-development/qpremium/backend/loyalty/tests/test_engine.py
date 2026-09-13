from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from clients.models import Client
from loyalty.engine import (
    apply_adjustment,
    apply_redemption,
    confirm_accrual,
    create_accrual,
    floor_points,
    grant_gift,
    patch_pending_accrual,
    preview_redemption,
)
from loyalty.models import BonusLot, ProgramSettings
from loyalty.timeutils import end_of_moscow_day, moscow_today
from stores.models import Store


class EngineTests(TestCase):
    def setUp(self):
        ProgramSettings.get_solo()
        self.store = Store.objects.create(name="S1", address="A1")
        self.client_obj = Client.objects.create(
            telegram_id=1001,
            full_name="Test User",
            phone="+79001112233",
            email="t@example.com",
            birth_date=date(1990, 1, 1),
        )

    def test_floor(self):
        self.assertEqual(floor_points(Decimal("10001"), Decimal("5")), 500)

    def test_accrual_confirm_and_redeem(self):
        op = create_accrual(
            client=self.client_obj,
            purchase_amount=Decimal("10000"),
            store=self.store,
            operator_telegram_id=1,
            idempotency_key="k1",
        )
        self.assertEqual(op.points, 500)
        self.assertEqual(op.status, "PENDING")
        confirm_accrual(op)
        prev = preview_redemption(client=self.client_obj, purchase_amount=Decimal("5000"))
        self.assertEqual(prev["to_redeem"], 500)  # balance 500 < 1500 cap
        op2, to_redeem = apply_redemption(
            client=self.client_obj,
            purchase_amount=Decimal("5000"),
            store=self.store,
            operator_telegram_id=1,
            idempotency_key="k2",
        )
        self.assertEqual(to_redeem, 500)
        self.assertEqual(op2.points, -500)

    def test_gift_and_adjustment(self):
        gift = grant_gift(
            client=self.client_obj,
            points=100,
            op_type="GIFT_ACCRUAL",
        )
        self.assertEqual(gift.points, 100)
        adj = apply_adjustment(
            client=self.client_obj,
            points=-40,
            point_type="gift",
            comment="corr",
            operator_telegram_id=1,
        )
        self.assertEqual(adj.points, -40)
        lot = BonusLot.objects.get(source_operation=gift)
        self.assertEqual(lot.remaining_points, 60)

    def test_patch_pending(self):
        op = create_accrual(
            client=self.client_obj,
            purchase_amount=Decimal("10000"),
            store=self.store,
            operator_telegram_id=1,
            idempotency_key="k-patch",
        )
        op = patch_pending_accrual(op, purchase_amount=Decimal("20000"))
        self.assertEqual(op.points, 1000)
        op = patch_pending_accrual(op, points=777, override_reason="manual")
        self.assertEqual(op.points, 777)
        self.assertEqual(op.override_reason, "manual")
