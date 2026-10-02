# -*- coding: utf-8 -*-
"""ADMIN-only REST endpoints: stores, access, clients, settings, stats, backup."""

from __future__ import annotations

import io
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.response import Response
from rest_framework.views import APIView

from clients.models import Client, ConsentRecord
from loyalty.engine import (
    EngineError,
    apply_adjustment,
    balance_breakdown,
    grant_gift,
    patch_pending_accrual,
)
from loyalty.models import (
    Broadcast,
    BroadcastDelivery,
    Operation,
    ProfileChangeRequest,
    ProgramSettings,
    Promotion,
)
from loyalty.notify import notify_client_gift, schedule_broadcast
from loyalty.permissions import IsAdmin
from loyalty.throttles import BroadcastRateThrottle
from loyalty.timefmt import format_moscow_date, format_moscow_dt, to_moscow_iso
from loyalty.views import _audit, _dec, _op_json
from stores.models import AdminUser, Store, StoreAccess


def _page(qs, request, serializer):
    try:
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(100, max(1, int(request.query_params.get("page_size", 50))))
    except (TypeError, ValueError):
        page, page_size = 1, 50
    total = qs.count()
    start = (page - 1) * page_size
    items = list(qs[start : start + page_size])
    return Response(
        {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": [serializer(x) for x in items],
        }
    )


def _store_json(s: Store) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "address": s.address,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


def _access_json(a: StoreAccess) -> dict:
    client = Client.objects.filter(telegram_id=a.telegram_id).first()
    return {
        "id": str(a.id),
        "store_id": str(a.store_id),
        "store_name": a.store.name,
        "store_address": a.store.address or "",
        "telegram_id": a.telegram_id,
        "phone": client.phone if client else "",
        "full_name": client.full_name if client else "",
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat(),
    }


def _parse_telegram_id(raw) -> int:
    text = str(raw or "").strip().replace(" ", "")
    if text.startswith("@"):
        raise EngineError(
            "validation_error",
            "Нужен числовой Telegram ID, не @username. Узнать ID: бот @userinfobot",
            400,
        )
    if not text.isdigit():
        raise EngineError("validation_error", "Telegram ID — только цифры", 400)
    return int(text)


def _admin_json(a: AdminUser) -> dict:
    return {
        "id": str(a.id),
        "telegram_id": a.telegram_id,
        "display_name": a.display_name,
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat(),
    }


def _settings_json(s: ProgramSettings, request=None) -> dict:
    photo_url = ""
    if s.bot_welcome_photo:
        if request is not None:
            photo_url = request.build_absolute_uri(s.bot_welcome_photo.url)
        else:
            photo_url = s.bot_welcome_photo.url
    return {
        "accrual_percent": str(s.accrual_percent),
        "max_redeem_percent": str(s.max_redeem_percent),
        "min_purchase_amount": str(s.min_purchase_amount),
        "earned_ttl_days": s.earned_ttl_days,
        "gift_ttl_days": s.gift_ttl_days,
        "registration_gift_points": s.registration_gift_points,
        "birthday_gift_points": s.birthday_gift_points,
        "birthday_message_template": s.birthday_message_template,
        "points_expiry_warning_days": s.points_expiry_warning_days,
        "points_expiry_warning_template": s.points_expiry_warning_template,
        "rules_text": s.rules_text,
        "promotions_text": s.promotions_text,
        "bot_welcome_text": s.bot_welcome_text,
        "bot_welcome_photo_url": photo_url,
        "updated_at": to_moscow_iso(s.updated_at),
        "updated_by_telegram_id": s.updated_by_telegram_id,
    }


def _promo_json(p: Promotion) -> dict:
    return {
        "id": str(p.id),
        "title": p.title,
        "conditions_text": p.conditions_text,
        "body_text": p.body_text,
        "unit": p.unit,
        "unit_label": "%" if p.unit == Promotion.Unit.PERCENT else "₽",
        "value": str(p.value),
        "is_active": p.is_active,
        "sort_order": p.sort_order,
    }


def _client_list_json(c: Client) -> dict:
    return {
        "id": str(c.id),
        "full_name": c.full_name,
        "phone": c.phone,
        "email": c.email,
        "status": c.status,
        "registered_at": c.registered_at.isoformat(),
        "balance_total": balance_breakdown(c.id)["total"],
    }


class StoreListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        items = list(Store.objects.all().order_by("name", "created_at"))
        return Response(
            {
                "count": len(items),
                "page": 1,
                "page_size": len(items) or 1,
                "results": [_store_json(s) for s in items],
            }
        )

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        address = (request.data.get("address") or "").strip()
        if not name:
            raise EngineError("validation_error", "name обязателен", 400)
        if Store.objects.filter(name__iexact=name).exists():
            raise EngineError("conflict", "Магазин с таким названием уже есть", 409)
        store = Store.objects.create(name=name, address=address, is_active=True)
        _audit(request, "STORE_CREATED", "store", store.id)
        return Response(_store_json(store), status=201)


class StorePatchView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        store = get_object_or_404(Store, pk=pk)
        if "name" in request.data:
            name = str(request.data["name"]).strip()
            if not name:
                raise EngineError("validation_error", "name обязателен", 400)
            if Store.objects.filter(name__iexact=name).exclude(pk=store.pk).exists():
                raise EngineError("conflict", "Магазин с таким названием уже есть", 409)
            store.name = name
        if "address" in request.data:
            store.address = str(request.data["address"]).strip()
        if "is_active" in request.data:
            store.is_active = bool(request.data["is_active"])
        store.save()
        _audit(request, "STORE_UPDATED", "store", store.id)
        return Response(_store_json(store))

    def delete(self, request, pk):
        """Строка магазина удаляется из базы. История операций хранит снимок названия."""
        store = get_object_or_404(Store, pk=pk)
        store_id = store.id
        name = store.name
        with transaction.atomic():
            store.delete()
        if Store.objects.filter(pk=store_id).exists():
            raise EngineError("internal_error", "Магазин не удалился из базы", 500)
        _audit(request, "STORE_DELETED", "store", store_id, {"name": name, "hard": True})
        return Response({"ok": True, "id": str(store_id)})


class StoreAccessListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = StoreAccess.objects.select_related("store").filter(is_active=True).order_by("-created_at")
        store_id = request.query_params.get("store_id")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return _page(qs, request, _access_json)

    def post(self, request):
        store_id = request.data.get("store_id")
        store = get_object_or_404(Store, pk=store_id, is_active=True)

        phone_raw = (request.data.get("phone") or "").strip()
        telegram_raw = request.data.get("telegram_id")
        telegram_id = None
        client = None

        if phone_raw:
            from clients.services import normalize_phone

            phone = normalize_phone(phone_raw)
            client = Client.objects.by_phone(phone).first()
            if not client:
                raise EngineError(
                    "not_found",
                    "Клиент с таким телефоном не найден. Кассир сначала должен зарегистрироваться в программе (открыть Mini App и пройти регистрацию), затем привязка по его номеру.",
                    404,
                )
            telegram_id = client.telegram_id
        elif telegram_raw is not None and str(telegram_raw).strip() != "":
            try:
                telegram_id = int(str(telegram_raw).strip())
            except (TypeError, ValueError) as exc:
                raise EngineError("validation_error", "Некорректный Telegram ID", 400) from exc
            client = Client.objects.filter(telegram_id=telegram_id).first()
        else:
            raise EngineError(
                "validation_error",
                "Укажите телефон кассира (он должен быть уже зарегистрирован в программе)",
                400,
            )

        with transaction.atomic():
            if AdminUser.objects.select_for_update().filter(telegram_id=telegram_id, is_active=True).exists():
                raise EngineError(
                    "role_conflict",
                    "Этот пользователь — администратор. Админа нельзя сделать кассиром.",
                    409,
                )
            existing = StoreAccess.objects.select_for_update().filter(telegram_id=telegram_id).first()
            if existing:
                if existing.is_active and str(existing.store_id) == str(store.id):
                    raise EngineError(
                        "conflict",
                        "Этот кассир уже привязан к этому магазину.",
                        409,
                    )
                existing.store = store
                existing.is_active = True
                existing.save(update_fields=["store", "is_active"])
                access = existing
                _audit(request, "STORE_ACCESS_UPDATED", "store_access", access.id)
                return Response(_access_json(access))
            access = StoreAccess.objects.create(
                store=store,
                telegram_id=telegram_id,
                created_by_telegram_id=request.actor.telegram_id,
            )
        _audit(
            request,
            "STORE_ACCESS_CREATED",
            "store_access",
            access.id,
            {"telegram_id": telegram_id, "store_id": str(store.id)},
        )
        return Response(_access_json(access), status=201)


class StoreAccessPatchView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        access = get_object_or_404(StoreAccess.objects.select_related("store"), pk=pk)
        if "is_active" in request.data:
            access.is_active = bool(request.data["is_active"])
        if "store_id" in request.data:
            access.store = get_object_or_404(Store, pk=request.data["store_id"], is_active=True)
        access.save()
        _audit(request, "STORE_ACCESS_UPDATED", "store_access", access.id)
        return Response(_access_json(access))

    def delete(self, request, pk):
        access = get_object_or_404(StoreAccess.objects.select_related("store"), pk=pk)
        access_id = access.id
        payload = {
            "telegram_id": access.telegram_id,
            "store_id": str(access.store_id),
            "store_name": access.store.name,
        }
        access.delete()
        _audit(request, "STORE_ACCESS_DELETED", "store_access", access_id, payload)
        return Response({"ok": True, "id": str(access_id)})


class AdminListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = AdminUser.objects.all().order_by("-created_at")
        return _page(qs, request, _admin_json)

    def post(self, request):
        telegram_id = _parse_telegram_id(request.data.get("telegram_id"))
        display_name = (request.data.get("display_name") or "").strip()
        with transaction.atomic():
            StoreAccess.objects.select_for_update().filter(
                telegram_id=telegram_id, is_active=True
            ).update(is_active=False)
            existing = AdminUser.objects.filter(telegram_id=telegram_id).first()
            if existing:
                if existing.is_active:
                    raise EngineError("conflict", "Этот Telegram ID уже администратор", 409)
                existing.is_active = True
                if display_name:
                    existing.display_name = display_name
                existing.save()
                admin = existing
                _audit(request, "ADMIN_REACTIVATED", "admin", admin.id)
                return Response(_admin_json(admin), status=200)
            admin = AdminUser.objects.create(telegram_id=telegram_id, display_name=display_name)
        _audit(request, "ADMIN_CREATED", "admin", admin.id)
        return Response(_admin_json(admin), status=201)


class AdminPatchView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        with transaction.atomic():
            admin = get_object_or_404(AdminUser.objects.select_for_update(), pk=pk)
            if "display_name" in request.data:
                admin.display_name = str(request.data["display_name"]).strip()
            if "is_active" in request.data:
                want_active = bool(request.data["is_active"])
                if not want_active and admin.is_active:
                    active_count = AdminUser.objects.select_for_update().filter(is_active=True).count()
                    if active_count <= 1:
                        raise EngineError("last_admin", "Нельзя деактивировать последнего ADMIN", 409)
                admin.is_active = want_active
            admin.save()
        _audit(request, "ADMIN_UPDATED", "admin", admin.id)
        return Response(_admin_json(admin))

    def delete(self, request, pk):
        with transaction.atomic():
            admin = get_object_or_404(AdminUser.objects.select_for_update(), pk=pk)
            if admin.is_active:
                active_count = AdminUser.objects.select_for_update().filter(is_active=True).count()
                if active_count <= 1:
                    raise EngineError("last_admin", "Нельзя удалить последнего активного ADMIN", 409)
            admin_id = admin.id
            admin.delete()
        _audit(request, "ADMIN_DELETED", "admin", admin_id)
        return Response(status=204)


class SettingsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(_settings_json(ProgramSettings.get_solo(), request))

    def patch(self, request):
        s = ProgramSettings.get_solo()
        before = _settings_json(s, request)
        decimal_fields = ("accrual_percent", "max_redeem_percent", "min_purchase_amount")
        int_fields = (
            "earned_ttl_days",
            "gift_ttl_days",
            "registration_gift_points",
            "birthday_gift_points",
            "points_expiry_warning_days",
        )
        text_fields = (
            "birthday_message_template",
            "points_expiry_warning_template",
            "rules_text",
            "promotions_text",
            "bot_welcome_text",
        )
        for f in decimal_fields:
            if f in request.data:
                setattr(s, f, _dec(request.data[f]))
        for f in int_fields:
            if f in request.data:
                setattr(s, f, int(request.data[f]))
        for f in text_fields:
            if f in request.data:
                setattr(s, f, str(request.data[f]))
        if request.FILES.get("bot_welcome_photo"):
            photo = request.FILES["bot_welcome_photo"]
            content_type = getattr(photo, "content_type", "") or ""
            if not content_type.startswith("image/"):
                raise EngineError("validation_error", "Файл приветствия должен быть изображением", 400)
            if photo.size and photo.size > 5 * 1024 * 1024:
                raise EngineError("validation_error", "Фото приветствия не больше 5 МБ", 400)
            if s.bot_welcome_photo:
                s.bot_welcome_photo.delete(save=False)
            s.bot_welcome_photo = photo
        elif str(request.data.get("clear_bot_welcome_photo", "")).lower() in ("true", "1", "yes"):
            if s.bot_welcome_photo:
                s.bot_welcome_photo.delete(save=False)
            s.bot_welcome_photo = None
        s.updated_by_telegram_id = request.actor.telegram_id
        s.save()
        after = _settings_json(s, request)
        diff = {k: {"from": before[k], "to": after[k]} for k in after if before.get(k) != after.get(k)}
        _audit(request, "SETTINGS_CHANGED", "settings", 1, {"diff_keys": list(diff.keys())})
        return Response(after)


class ClientListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Client.objects.all().order_by("-registered_at")
        q = (request.query_params.get("q") or "").strip()
        field = request.query_params.get("field", "name")
        if q:
            if field == "phone":
                from clients.services import normalize_phone

                try:
                    phone_n = normalize_phone(q)
                except EngineError:
                    qs = qs.none()
                else:
                    hit = Client.objects.by_phone(phone_n).first()
                    qs = qs.filter(pk=hit.pk) if hit else qs.none()
            else:
                needle = q.lower()
                ids = [c.pk for c in qs.only("id", "full_name") if needle in (c.full_name or "").lower()]
                qs = qs.filter(pk__in=ids)
        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return _page(qs, request, _client_list_json)


class ClientOperationsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        qs = Operation.objects.filter(client=client).order_by("-created_at")
        return _page(qs, request, _op_json)


class ClientGiftView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        try:
            points = int(request.data.get("points"))
        except (TypeError, ValueError) as exc:
            raise EngineError("validation_error", "points обязателен", 400) from exc
        comment = (request.data.get("comment") or "").strip()
        op = grant_gift(
            client=client,
            points=points,
            op_type=Operation.Type.GIFT_ACCRUAL,
            operator_telegram_id=request.actor.telegram_id,
            comment=comment,
        )
        _audit(request, "GIFT_GRANTED", "operation", op.id, {"points": points})
        bal = balance_breakdown(client.id)
        notify_client_gift(client, points=points, balance_total=bal["total"])
        return Response({"operation": _op_json(op), "balance": bal}, status=201)


class ClientAdjustmentView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        try:
            points = int(request.data.get("points"))
        except (TypeError, ValueError) as exc:
            raise EngineError("validation_error", "points обязателен", 400) from exc
        point_type = request.data.get("point_type") or "earned"
        comment = request.data.get("comment") or ""
        op = apply_adjustment(
            client=client,
            points=points,
            point_type=point_type,
            comment=comment,
            operator_telegram_id=request.actor.telegram_id,
        )
        _audit(request, "ADJUSTMENT_APPLIED", "operation", op.id, {"points": points})
        return Response({"operation": _op_json(op), "balance": balance_breakdown(client.id)}, status=201)


def build_clients_export_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Клиенты"
    ws.append(
        [
            "ФИО",
            "Телефон",
            "Email",
            "Дата рождения",
            "Статус",
            "Дата регистрации",
            "Накопительные баллы",
            "Подарочные баллы",
            "Всего баллов",
        ]
    )
    for c in Client.objects.all().order_by("registered_at"):
        bal = balance_breakdown(c.id)
        ws.append(
            [
                c.full_name,
                c.phone,
                c.email,
                format_moscow_date(c.birth_date),
                "активен" if c.status == Client.Status.ACTIVE else "заблокирован",
                format_moscow_dt(c.registered_at),
                bal["earned"],
                bal["gift"],
                bal["total"],
            ]
        )
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def latest_backup_file() -> Path:
    from loyalty.tasks import create_db_backup

    backup_dir = Path(os.environ.get("BACKUP_DIR") or getattr(settings, "BACKUP_DIR", "/backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    dumps = sorted(backup_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dumps:
        dumps = sorted(backup_dir.glob("*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dumps:
        result = create_db_backup()
        if result.get("error"):
            raise EngineError("not_found", f"Не удалось создать резервную копию: {result['error']}", 404)
        dumps = sorted(backup_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not dumps:
            dumps = sorted(backup_dir.glob("*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dumps:
        raise EngineError("not_found", "Файл резервной копии не найден", 404)
    return dumps[0]


def _bot_admin_actor(request):
    """Сервисный вызов бота: только ADMIN. Возвращает (actor, error_response)."""
    from loyalty.authentication import resolve_actor, verify_bot_internal_secret

    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not verify_bot_internal_secret(auth_header):
        return None, Response(
            {"error": {"code": "forbidden", "message": "Неверный bot secret", "details": {}}},
            status=403,
        )
    try:
        telegram_id = int(request.query_params.get("telegram_id"))
    except (TypeError, ValueError):
        return None, Response(
            {"error": {"code": "validation_error", "message": "telegram_id обязателен", "details": {}}},
            status=400,
        )
    actor = resolve_actor(telegram_id)
    if actor.role != "ADMIN":
        return None, Response(
            {"error": {"code": "forbidden", "message": "Только для администратора", "details": {}}},
            status=403,
        )
    request.actor = actor
    return actor, None


class ClientExportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        payload = build_clients_export_bytes()
        _audit(request, "CLIENT_EXPORT", "clients", "all")
        resp = HttpResponse(
            payload,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = 'attachment; filename="clients_export.xlsx"'
        return resp


class OperationsListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Operation.objects.all().order_by("-created_at")
        for key, field in (
            ("type", "type"),
            ("status", "status"),
            ("store_id", "store_id"),
            ("client_id", "client_id"),
        ):
            val = request.query_params.get(key)
            if val:
                qs = qs.filter(**{field: val})
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return _page(qs, request, _op_json)


class OperationDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        op = get_object_or_404(Operation, pk=pk)
        data = _op_json(op)
        data["comment"] = op.comment
        data["override_reason"] = op.override_reason
        return Response(data)

    def patch(self, request, pk):
        op = get_object_or_404(Operation, pk=pk)
        purchase_amount = None
        points = None
        if "purchase_amount" in request.data:
            purchase_amount = _dec(request.data.get("purchase_amount"))
        if "points" in request.data:
            try:
                points = int(request.data.get("points"))
            except (TypeError, ValueError) as exc:
                raise EngineError("validation_error", "Некорректные points", 400) from exc
        op = patch_pending_accrual(
            op,
            purchase_amount=purchase_amount,
            points=points,
            override_reason=request.data.get("override_reason") or "",
        )
        _audit(request, "ACCRUAL_PATCHED", "operation", op.id)
        return Response(_op_json(op))


class StatisticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        period = request.query_params.get("period") or "month"
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        if period == "week":
            start = now - timedelta(days=7)
            end = now
        elif period == "month":
            start = now - timedelta(days=30)
            end = now
        elif period == "year":
            start = now - timedelta(days=365)
            end = now
        elif period == "custom" or (date_from and date_to):
            if not date_from or not date_to:
                raise EngineError("validation_error", "Для произвольного периода нужны from и to (YYYY-MM-DD)", 400)
            try:
                start = timezone.make_aware(datetime.fromisoformat(date_from))
                end = timezone.make_aware(datetime.fromisoformat(date_to)) + timedelta(days=1)
            except ValueError as exc:
                raise EngineError("validation_error", "Некорректные даты from/to", 400) from exc
            if end <= start:
                raise EngineError("validation_error", "Дата «по» должна быть не раньше «с»", 400)
        else:
            start = now - timedelta(days=30)
            end = now

        ops = Operation.objects.filter(created_at__gte=start, created_at__lt=end)
        confirmed = ops.filter(status=Operation.Status.CONFIRMED)
        accruals = confirmed.filter(type=Operation.Type.BONUS_ACCRUAL)
        redemptions = confirmed.filter(type=Operation.Type.BONUS_REDEMPTION)
        return Response(
            {
                "period": {"from": start.isoformat(), "to": end.isoformat(), "preset": period},
                "clients_total": Client.objects.count(),
                "clients_new": Client.objects.filter(registered_at__gte=start, registered_at__lt=end).count(),
                "accruals_count": accruals.count(),
                "accruals_points": accruals.aggregate(s=Sum("points"))["s"] or 0,
                "accruals_purchase_sum": str(accruals.aggregate(s=Sum("purchase_amount"))["s"] or Decimal("0")),
                "redemptions_count": redemptions.count(),
                "redemptions_points": abs(redemptions.aggregate(s=Sum("points"))["s"] or 0),
                "pending_count": Operation.objects.filter(
                    type=Operation.Type.BONUS_ACCRUAL, status=Operation.Status.PENDING
                ).count(),
                "by_store": list(
                    accruals.values("store_name_snapshot")
                    .annotate(count=Count("id"), points=Sum("points"))
                    .order_by("-points")
                ),
            }
        )


def _advertising_audience() -> list[Client]:
    """Clients whose latest ADVERTISING consent is accepted (DR-005)."""
    out: list[Client] = []
    for client in Client.objects.filter(status=Client.Status.ACTIVE):
        latest = (
            ConsentRecord.objects.filter(client=client, consent_type=ConsentRecord.ConsentType.ADVERTISING)
            .order_by("-created_at")
            .first()
        )
        if latest and latest.status == ConsentRecord.Status.ACCEPTED:
            out.append(client)
    return out


class BroadcastListCreateView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [BroadcastRateThrottle]

    def get(self, request):
        qs = Broadcast.objects.all().order_by("-created_at")
        return _page(
            qs,
            request,
            lambda b: {
                "id": str(b.id),
                "body": b.body,
                "audience_count": b.audience_count,
                "sent_count": b.sent_count,
                "created_by_telegram_id": b.created_by_telegram_id,
                "created_at": b.created_at.isoformat(),
                "meta": b.meta,
            },
        )

    def post(self, request):
        body = (request.data.get("body") or "").strip()
        if not body:
            raise EngineError("validation_error", "body обязателен", 400)
        if len(body) > 4096:
            raise EngineError("validation_error", "body максимум 4096 символов", 400)

        audience = _advertising_audience()
        with transaction.atomic():
            b = Broadcast.objects.create(
                body=body,
                audience_count=len(audience),
                sent_count=0,
                created_by_telegram_id=request.actor.telegram_id,
                meta={"status": "queued"},
            )
            BroadcastDelivery.objects.bulk_create(
                [
                    BroadcastDelivery(
                        broadcast=b,
                        client=c,
                        telegram_id=c.telegram_id,
                        status=BroadcastDelivery.Status.PENDING,
                    )
                    for c in audience
                ]
            )
            schedule_broadcast(b.id)

        _audit(request, "BROADCAST_CREATED", "broadcast", b.id, {"audience": len(audience)})
        return Response(
            {
                "id": str(b.id),
                "body": b.body,
                "audience_count": b.audience_count,
                "sent_count": b.sent_count,
                "note": "Рассылка уйдёт только клиентам, которые согласились получать рекламу.",
            },
            status=201,
        )


class BackupCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        from loyalty.tasks import create_db_backup

        result = create_db_backup()
        if result.get("error"):
            raise EngineError("internal_error", result["error"], 500)
        _audit(request, "BACKUP_CREATED", "backup", result.get("file", ""))
        return Response(result, status=201)


class BackupDownloadView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        latest = latest_backup_file()
        _audit(request, "BACKUP_DOWNLOAD", "backup", latest.name)
        return FileResponse(latest.open("rb"), as_attachment=True, filename=latest.name)


class BotClientExportView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        _actor, err = _bot_admin_actor(request)
        if err:
            return err
        payload = build_clients_export_bytes()
        _audit(request, "CLIENT_EXPORT", "clients", "all", {"via": "bot"})
        resp = HttpResponse(
            payload,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = 'attachment; filename="clients_export.xlsx"'
        return resp


class BotBackupDownloadView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        _actor, err = _bot_admin_actor(request)
        if err:
            return err
        latest = latest_backup_file()
        _audit(request, "BACKUP_DOWNLOAD", "backup", latest.name, {"via": "bot"})
        return FileResponse(latest.open("rb"), as_attachment=True, filename=latest.name)


class PromotionListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Promotion.objects.all()
        return _page(qs, request, _promo_json)

    def post(self, request):
        title = (request.data.get("title") or "").strip()
        if not title:
            raise EngineError("validation_error", "Укажите название акции", 400)
        unit = request.data.get("unit") or Promotion.Unit.PERCENT
        if unit not in (Promotion.Unit.PERCENT, Promotion.Unit.RUB):
            raise EngineError("validation_error", "Ед. изм.: percent или rub", 400)
        promo = Promotion.objects.create(
            title=title,
            conditions_text=(request.data.get("conditions_text") or "").strip(),
            body_text=(request.data.get("body_text") or "").strip(),
            unit=unit,
            value=_dec(request.data.get("value") or 0),
            is_active=bool(request.data.get("is_active", True)),
            sort_order=int(request.data.get("sort_order") or 0),
        )
        _audit(request, "PROMOTION_CREATED", "promotion", promo.id)
        return Response(_promo_json(promo), status=201)


class PromotionDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        for f in ("title", "conditions_text", "body_text"):
            if f in request.data:
                setattr(promo, f, str(request.data[f]).strip())
        if "unit" in request.data:
            promo.unit = request.data["unit"]
        if "value" in request.data:
            promo.value = _dec(request.data["value"])
        if "is_active" in request.data:
            promo.is_active = bool(request.data["is_active"])
        if "sort_order" in request.data:
            promo.sort_order = int(request.data["sort_order"])
        promo.save()
        _audit(request, "PROMOTION_UPDATED", "promotion", promo.id)
        return Response(_promo_json(promo))

    def delete(self, request, pk):
        promo = get_object_or_404(Promotion, pk=pk)
        promo.delete()
        _audit(request, "PROMOTION_DELETED", "promotion", pk)
        return Response({"ok": True})


class ProfileChangePendingView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = (
            ProfileChangeRequest.objects.filter(status=ProfileChangeRequest.Status.PENDING)
            .select_related("client")
            .order_by("created_at")
        )
        return _page(
            qs,
            request,
            lambda r: {
                "id": str(r.id),
                "client_id": str(r.client_id),
                "client_name": r.client.full_name,
                "client_phone": r.client.phone,
                "field": r.field,
                "field_label": "Дата рождения" if r.field == "birth_date" else r.field,
                "old_value": r.old_value,
                "new_value": r.new_value,
                "created_at": to_moscow_iso(r.created_at),
                "created_at_display": format_moscow_dt(r.created_at),
            },
        )


class ProfileChangeDecideView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        action = (request.data.get("action") or "").strip().lower()
        req = get_object_or_404(ProfileChangeRequest, pk=pk)
        if req.status != ProfileChangeRequest.Status.PENDING:
            raise EngineError("conflict", "Заявка уже обработана", 409)
        if action not in ("approve", "reject"):
            raise EngineError("validation_error", "action: approve|reject", 400)
        with transaction.atomic():
            req = ProfileChangeRequest.objects.select_for_update().get(pk=pk)
            if req.status != ProfileChangeRequest.Status.PENDING:
                raise EngineError("conflict", "Заявка уже обработана", 409)
            req.decided_at = timezone.now()
            req.decided_by_telegram_id = request.actor.telegram_id
            req.comment = (request.data.get("comment") or "").strip()
            if action == "approve":
                if req.field == "birth_date":
                    from clients.services import parse_and_validate_birth_date

                    req.client.birth_date = parse_and_validate_birth_date(req.new_value)
                    req.client.save(update_fields=["birth_date"])
                req.status = ProfileChangeRequest.Status.APPROVED
            else:
                req.status = ProfileChangeRequest.Status.REJECTED
            req.save()
        _audit(request, f"PROFILE_CHANGE_{req.status}", "profile_change", req.id)
        return Response(
            {
                "id": str(req.id),
                "status": req.status,
            }
        )
