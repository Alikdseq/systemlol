"""Regression: auth, RBAC, IDOR, store isolation, idempotency, FIFO, concurrent."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal

import jwt
from django.conf import settings
from django.db import close_old_connections, connection, transaction
from django.test import Client as HttpClient
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from clients.models import Client
from loyalty.authentication import issue_access_token, resolve_actor
from loyalty.engine import apply_redemption, confirm_accrual, create_accrual, EngineError
from loyalty.models import BonusLot, ProgramSettings
from stores.models import AdminUser, Store, StoreAccess


def _token(tg: int) -> str:
    return issue_access_token(resolve_actor(tg))


class AuthJwtTests(TestCase):
    def test_unsigned_init_data_401(self):
        r = self.client.post(
            "/api/v1/auth/telegram",
            data=json.dumps({"init_data": '{"id": 1}'}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "invalid_init_data")

    def test_telegram_id_alone_401(self):
        r = self.client.post(
            "/api/v1/auth/telegram",
            data=json.dumps({"telegram_id": 1}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_expired_jwt_401_token_expired(self):
        payload = {"tg": 1, "role": "NONE", "exp": int(time.time()) - 10, "iat": int(time.time()) - 100}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        r = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(r.status_code, 401, r.content)
        self.assertEqual(r.json()["error"]["code"], "token_expired")

    def test_invalid_jwt_401_unauthorized(self):
        r = self.client.get("/api/v1/auth/me", HTTP_AUTHORIZATION="Bearer not.a.jwt")
        self.assertEqual(r.status_code, 401, r.content)
        self.assertEqual(r.json()["error"]["code"], "unauthorized")


class RbacIdorStoreTests(TestCase):
    def setUp(self):
        ProgramSettings.get_solo()
        self.store_a = Store.objects.create(name="A", address="a")
        self.store_b = Store.objects.create(name="B", address="b")
        self.admin_tg = 88001
        self.store_tg = 88002
        self.client_tg = 88003
        self.other_tg = 88004
        AdminUser.objects.create(telegram_id=self.admin_tg, display_name="A", is_active=True)
        StoreAccess.objects.create(telegram_id=self.store_tg, store=self.store_a, is_active=True)
        self.client_obj = Client.objects.create(
            telegram_id=self.client_tg,
            full_name="C",
            phone="+79008800301",
            email="c@ex.com",
            birth_date=date(1990, 1, 1),
        )
        self.other = Client.objects.create(
            telegram_id=self.other_tg,
            full_name="O",
            phone="+79008800401",
            email="o@ex.com",
            birth_date=date(1991, 1, 1),
        )
        self.hc = HttpClient()

    def _h(self, tg):
        return {"HTTP_AUTHORIZATION": f"Bearer {_token(tg)}"}

    def test_client_cannot_lookup(self):
        r = self.hc.post(
            "/api/v1/clients/lookup",
            data=json.dumps({"phone": self.client_obj.phone}),
            content_type="application/json",
            **self._h(self.client_tg),
        )
        self.assertEqual(r.status_code, 403)

    def test_store_cannot_backup_or_export(self):
        r = self.hc.get("/api/v1/backups/latest/download", **self._h(self.store_tg))
        self.assertEqual(r.status_code, 403)
        r = self.hc.get("/api/v1/clients/export", **self._h(self.store_tg))
        self.assertEqual(r.status_code, 403)

    @override_settings(TELEGRAM_BOT_TOKEN="bot-test-secret")
    def test_bot_files_only_for_admin(self):
        store = self.hc.get(
            f"/api/v1/bot/admin/clients-export?telegram_id={self.store_tg}",
            HTTP_AUTHORIZATION="Bot bot-test-secret",
        )
        self.assertEqual(store.status_code, 403)
        wrong = self.hc.get(
            f"/api/v1/bot/admin/clients-export?telegram_id={self.admin_tg}",
            HTTP_AUTHORIZATION="Bot wrong",
        )
        self.assertEqual(wrong.status_code, 403)
        ok = self.hc.get(
            f"/api/v1/bot/admin/clients-export?telegram_id={self.admin_tg}",
            HTTP_AUTHORIZATION="Bot bot-test-secret",
        )
        self.assertEqual(ok.status_code, 200)
        self.assertIn("spreadsheetml", ok["Content-Type"])

    def test_store_cannot_read_admin_settings(self):
        r = self.hc.get("/api/v1/settings", **self._h(self.store_tg))
        self.assertEqual(r.status_code, 403)

    def test_store_lookup_has_no_email_or_birth(self):
        r = self.hc.post(
            "/api/v1/clients/lookup",
            data=json.dumps({"phone": self.client_obj.phone}),
            content_type="application/json",
            **self._h(self.store_tg),
        )
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertNotIn("email", body)
        self.assertNotIn("birth_date", body)

    def test_idor_client_detail(self):
        r = self.hc.get(f"/api/v1/clients/{self.other.id}", **self._h(self.store_tg))
        self.assertEqual(r.status_code, 403)
        r = self.hc.get(f"/api/v1/clients/{self.other.id}", **self._h(self.client_tg))
        self.assertEqual(r.status_code, 403)

    def test_store_cannot_spoof_store_id(self):
        r = self.hc.post(
            "/api/v1/accruals",
            data=json.dumps(
                {
                    "client_id": str(self.client_obj.id),
                    "purchase_amount": "5000",
                    "store_id": str(self.store_b.id),
                }
            ),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="rbac-spoof-1",
            **self._h(self.store_tg),
        )
        self.assertEqual(r.status_code, 403, r.content)

    def test_store_cannot_pass_points(self):
        r = self.hc.post(
            "/api/v1/accruals",
            data=json.dumps(
                {"client_id": str(self.client_obj.id), "purchase_amount": "5000", "points": 99}
            ),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="rbac-pts-1",
            **self._h(self.store_tg),
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "points_not_allowed")

    def test_admin_missing_store_id(self):
        r = self.hc.post(
            "/api/v1/accruals",
            data=json.dumps({"client_id": str(self.client_obj.id), "purchase_amount": "5000"}),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="rbac-adm-1",
            **self._h(self.admin_tg),
        )
        self.assertEqual(r.status_code, 400)

    def test_admin_store_access_conflict(self):
        r = self.hc.post(
            "/api/v1/store-accesses",
            data=json.dumps({"telegram_id": self.admin_tg, "store_id": str(self.store_a.id)}),
            content_type="application/json",
            **self._h(self.admin_tg),
        )
        self.assertEqual(r.status_code, 409)


class IdempotencyFifoTests(TestCase):
    def setUp(self):
        ProgramSettings.get_solo()
        self.store = Store.objects.create(name="S", address="s")
        self.client_obj = Client.objects.create(
            telegram_id=88101,
            full_name="I",
            phone="+79008810101",
            email="i@ex.com",
            birth_date=date(1990, 1, 1),
        )

    def test_idempotency_same_and_reuse(self):
        a = create_accrual(
            client=self.client_obj,
            purchase_amount=Decimal("10000"),
            store=self.store,
            operator_telegram_id=1,
            idempotency_key="idem-same",
        )
        b = create_accrual(
            client=self.client_obj,
            purchase_amount=Decimal("10000"),
            store=self.store,
            operator_telegram_id=1,
            idempotency_key="idem-same",
        )
        self.assertEqual(a.id, b.id)
        with self.assertRaises(EngineError) as ctx:
            create_accrual(
                client=self.client_obj,
                purchase_amount=Decimal("20000"),
                store=self.store,
                operator_telegram_id=1,
                idempotency_key="idem-same",
            )
        self.assertEqual(ctx.exception.code, "idempotency_key_reused")
        self.assertEqual(ctx.exception.http_status, 409)

    def test_fifo_redeem_250(self):
        now = timezone.now()
        lot_a = BonusLot.objects.create(
            client=self.client_obj,
            point_type="earned",
            initial_points=100,
            remaining_points=100,
            accrued_at=now - timedelta(days=3),
            expires_at=now + timedelta(days=5),
        )
        lot_b = BonusLot.objects.create(
            client=self.client_obj,
            point_type="earned",
            initial_points=200,
            remaining_points=200,
            accrued_at=now - timedelta(days=2),
            expires_at=now + timedelta(days=30),
        )
        lot_c = BonusLot.objects.create(
            client=self.client_obj,
            point_type="earned",
            initial_points=300,
            remaining_points=300,
            accrued_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=40),
        )
        _op, redeemed = apply_redemption(
            client=self.client_obj,
            purchase_amount=Decimal("834"),
            store=self.store,
            operator_telegram_id=1,
            idempotency_key="fifo-250",
        )
        lot_a.refresh_from_db()
        lot_b.refresh_from_db()
        lot_c.refresh_from_db()
        self.assertEqual(redeemed, 250)
        self.assertEqual(lot_a.remaining_points, 0)
        self.assertEqual(lot_b.remaining_points, 50)
        self.assertEqual(lot_c.remaining_points, 300)


class ConcurrentRedemptionTests(TransactionTestCase):
    def setUp(self):
        ProgramSettings.get_solo()
        self.store = Store.objects.create(name="SC", address="sc")
        self.client_obj = Client.objects.create(
            telegram_id=88201,
            full_name="K",
            phone="+79008820101",
            email="k@ex.com",
            birth_date=date(1990, 1, 1),
        )
        now = timezone.now()
        BonusLot.objects.create(
            client=self.client_obj,
            point_type="gift",
            initial_points=500,
            remaining_points=500,
            accrued_at=now,
            expires_at=now + timedelta(days=20),
        )

    def test_two_full_redeems_one_success(self):
        if connection.vendor != "postgresql":
            self.skipTest("SELECT FOR UPDATE concurrent proof requires PostgreSQL")

        cid = self.client_obj.id
        sid = self.store.id

        def job(i):
            close_old_connections()
            store = Store.objects.get(pk=sid)
            client = Client.objects.get(pk=cid)
            try:
                apply_redemption(
                    client=client,
                    purchase_amount=Decimal("10000"),
                    store=store,
                    operator_telegram_id=1,
                    idempotency_key=f"conc-{i}-{time.time_ns()}",
                )
                return "ok"
            except EngineError:
                return "err"

        with ThreadPoolExecutor(max_workers=2) as ex:
            results = list(ex.map(job, [0, 1]))
        self.assertEqual(sorted(results), ["err", "ok"], results)
        from loyalty.engine import get_available_balance

        self.assertGreaterEqual(get_available_balance(cid), 0)
        self.assertEqual(get_available_balance(cid), 0)


class BonusLotConstraintTests(TestCase):
    def setUp(self):
        ProgramSettings.get_solo()
        self.client_obj = Client.objects.create(
            telegram_id=88301,
            full_name="L",
            phone="+79008830101",
            email="l@ex.com",
            birth_date=date(1990, 1, 1),
        )

    def test_remaining_cannot_exceed_initial(self):
        lot = BonusLot.objects.create(
            client=self.client_obj,
            point_type="gift",
            initial_points=10,
            remaining_points=10,
            accrued_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=1),
        )
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE loyalty_bonuslot SET remaining_points = initial_points + 5 WHERE id = %s",
                        [str(lot.id)],
                    )
