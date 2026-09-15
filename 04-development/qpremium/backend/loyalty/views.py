from decimal import Decimal, InvalidOperation

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditLog
from clients.models import Client
from clients.services import (
    advertising_accepted,
    consent_proof_summary,
    consents_for_display,
    normalize_phone,
    register_client,
    set_advertising_consent,
)
from datetime import date as date_cls
from django.conf import settings
from django.utils import timezone
from loyalty.authentication import (
    TelegramJWTAuthentication,
    issue_access_token,
    resolve_actor,
    verify_bot_internal_secret,
    verify_telegram_init_data,
)
from loyalty.throttles import AuthRateThrottle, BroadcastRateThrottle, LookupRateThrottle
from loyalty.engine import (
    EngineError,
    apply_redemption,
    balance_breakdown,
    confirm_accrual,
    create_accrual,
    preview_redemption,
    reject_accrual,
    resolve_operator_name,
)
from loyalty.models import Operation, ProfileChangeRequest, ProgramSettings, Promotion
from loyalty.notify import (
    notify_client_after_confirm,
    notify_client_after_redeem,
    notify_client_after_reject,
)
from loyalty.permissions import CanRegister, IsAdmin, IsClient, IsNoneRole, IsStore
from loyalty.timefmt import format_moscow_dt, to_moscow_iso
from stores.models import Store


def _audit(request, action, entity_type="", entity_id="", metadata=None):
    actor = getattr(request, "actor", None)
    AuditLog.objects.create(
        actor_telegram_id=getattr(actor, "telegram_id", None),
        actor_role=getattr(actor, "role", ""),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {},
        request_id=getattr(request, "request_id", ""),
    )


def _dec(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise EngineError("validation_error", "Некорректная сумма", 400) from exc


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def health(_request):
    return Response({"status": "ok"})


class AuthTelegramView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        init_data = request.data.get("init_data", "")
        try:
            verified = verify_telegram_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
            telegram_id = int(verified["user"]["id"])
        except Exception:
            _audit(request, "AUTH_FAIL")
            return Response(
                {"error": {"code": "invalid_init_data", "message": "Невалидные данные Telegram", "details": {}, "request_id": getattr(request, "request_id", "")}},
                status=401,
            )
        actor = resolve_actor(telegram_id)
        token = issue_access_token(actor)
        _audit(request, "AUTH_SUCCESS", metadata={"role": actor.role})
        store = None
        if actor.role == "STORE" and actor.store_id:
            store = {"id": actor.store_id, "name": actor.store_name, "address": actor.store_address}
        return Response(
            {
                "access_token": token,
                "expires_in": settings.ACCESS_TOKEN_TTL_SEC,
                "role": actor.role,
                "store": store,
                "user": {
                    "telegram_id": telegram_id,
                    "client_id": actor.client_id,
                    "has_client_profile": bool(actor.client_id),
                    "can_register": actor.client_id is None,
                },
            }
        )


class BotResolveRoleView(APIView):
    """Внутренний вызов бота: Authorization: Bot <TELEGRAM_BOT_TOKEN>, body telegram_id."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not verify_bot_internal_secret(auth_header):
            return Response(
                {"error": {"code": "forbidden", "message": "Неверный bot secret", "details": {}}},
                status=403,
            )
        try:
            telegram_id = int(request.data.get("telegram_id"))
        except (TypeError, ValueError):
            return Response(
                {"error": {"code": "validation_error", "message": "telegram_id обязателен", "details": {}}},
                status=400,
            )
        actor = resolve_actor(telegram_id)
        return Response({"telegram_id": telegram_id, "role": actor.role})


class AuthMeView(APIView):
    def get(self, request):
        a = request.actor
        return Response(
            {
                "telegram_id": a.telegram_id,
                "role": a.role,
                "store_id": a.store_id,
                "client_id": a.client_id,
            }
        )


class RegisterView(APIView):
    permission_classes = [CanRegister]

    def post(self, request):
        data = request.data
        client = register_client(
            telegram_id=request.actor.telegram_id,
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            birth_date=data.get("birth_date"),
            consents=data.get("consents") or {},
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        _audit(request, "CLIENT_REGISTERED", "client", client.id)
        _audit(request, "CONSENT_ACCEPTED", "client", client.id, {"types": list((data.get("consents") or {}).keys())})
        return Response(
            {
                "client": {
                    "id": str(client.id),
                    "full_name": client.full_name,
                    "phone": client.phone,
                    "email": client.email,
                    "birth_date": str(client.birth_date),
                },
                "consents": consent_proof_summary(client),
                "balance": balance_breakdown(client.id),
                "note": "Повторно вызовите POST /auth/telegram для token с client_id",
            },
            status=201,
        )


class ClientMeView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        client = get_object_or_404(Client, telegram_id=request.actor.telegram_id)
        pending_birth = (
            ProfileChangeRequest.objects.filter(
                client=client,
                field="birth_date",
                status=ProfileChangeRequest.Status.PENDING,
            )
            .order_by("-created_at")
            .first()
        )
        return Response(
            {
                "id": str(client.id),
                "full_name": client.full_name,
                "phone": client.phone,
                "email": client.email,
                "birth_date": str(client.birth_date),
                "advertising_accepted": advertising_accepted(client),
                "pending_birth_date": pending_birth.new_value if pending_birth else None,
                "pending_birth_date_id": str(pending_birth.id) if pending_birth else None,
            }
        )

    def patch(self, request):
        client = get_object_or_404(Client, telegram_id=request.actor.telegram_id)
        birth_pending_msg = None
        for field in ("full_name", "email"):
            if field in request.data:
                setattr(client, field, request.data[field])
        if "phone" in request.data:
            client.phone = normalize_phone(request.data["phone"])
        if "email" in request.data:
            client.email = str(request.data["email"]).strip().lower()

        if "birth_date" in request.data:
            raw = request.data.get("birth_date")
            try:
                new_bd = date_cls.fromisoformat(str(raw))
            except (TypeError, ValueError) as exc:
                raise EngineError("validation_error", "Некорректная дата рождения", 400) from exc
            if new_bd != client.birth_date:
                # ADMIN меняет свою ДР сразу; клиент/кассир — только через подтверждение
                if request.actor.role == "ADMIN":
                    client.birth_date = new_bd
                    ProfileChangeRequest.objects.filter(
                        client=client,
                        field="birth_date",
                        status=ProfileChangeRequest.Status.PENDING,
                    ).update(
                        status=ProfileChangeRequest.Status.APPROVED,
                        decided_at=timezone.now(),
                        decided_by_telegram_id=request.actor.telegram_id,
                        comment="Изменено администратором в своём профиле",
                    )
                    birth_pending_msg = "Дата рождения обновлена"
                    _audit(
                        request,
                        "PROFILE_BIRTH_UPDATED_BY_ADMIN",
                        "client",
                        client.id,
                        {"field": "birth_date"},
                    )
                else:
                    existing = ProfileChangeRequest.objects.filter(
                        client=client,
                        field="birth_date",
                        status=ProfileChangeRequest.Status.PENDING,
                    ).first()
                    if existing:
                        existing.new_value = new_bd.isoformat()
                        existing.save(update_fields=["new_value"])
                    else:
                        ProfileChangeRequest.objects.create(
                            client=client,
                            field="birth_date",
                            old_value=client.birth_date.isoformat(),
                            new_value=new_bd.isoformat(),
                        )
                    birth_pending_msg = (
                        "Запрос на смену даты рождения отправлен администратору. "
                        "До подтверждения действует текущая дата."
                    )
                    _audit(
                        request,
                        "PROFILE_CHANGE_REQUESTED",
                        "client",
                        client.id,
                        {"field": "birth_date"},
                    )

        client.save()
        pending_birth = (
            ProfileChangeRequest.objects.filter(
                client=client,
                field="birth_date",
                status=ProfileChangeRequest.Status.PENDING,
            )
            .order_by("-created_at")
            .first()
        )
        return Response(
            {
                "id": str(client.id),
                "full_name": client.full_name,
                "phone": client.phone,
                "email": client.email,
                "birth_date": str(client.birth_date),
                "advertising_accepted": advertising_accepted(client),
                "pending_birth_date": pending_birth.new_value if pending_birth else None,
                "note": birth_pending_msg,
            }
        )


class ClientAdvertisingView(APIView):
    """Тумблер согласия на рекламу (append-only accepted/revoked)."""

    permission_classes = [IsClient]

    def post(self, request):
        client = get_object_or_404(Client, telegram_id=request.actor.telegram_id)
        if "accepted" not in request.data:
            raise EngineError("validation_error", "Укажите accepted: true|false", 400)
        accepted = bool(request.data.get("accepted"))
        result = set_advertising_consent(
            client,
            accepted=accepted,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        _audit(
            request,
            "ADVERTISING_ACCEPTED" if result else "ADVERTISING_REVOKED",
            "client",
            client.id,
        )
        return Response({"advertising_accepted": result})


class ClientBalanceView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        client = get_object_or_404(Client, telegram_id=request.actor.telegram_id)
        return Response(balance_breakdown(client.id))


class PublicSettingsView(APIView):
    def get(self, request):
        s = ProgramSettings.get_solo()
        promos = Promotion.objects.filter(is_active=True).order_by("sort_order", "-created_at")
        return Response(
            {
                "accrual_percent": str(s.accrual_percent),
                "max_redeem_percent": str(s.max_redeem_percent),
                "min_purchase_amount": str(s.min_purchase_amount),
                "earned_ttl_days": s.earned_ttl_days,
                "gift_ttl_days": s.gift_ttl_days,
                "rules_text": s.rules_text,
                "promotions_text": s.promotions_text,
                "promotions": [
                    {
                        "id": str(p.id),
                        "title": p.title,
                        "conditions_text": p.conditions_text,
                        "body_text": p.body_text,
                        "unit": p.unit,
                        "unit_label": "%" if p.unit == Promotion.Unit.PERCENT else "₽",
                        "value": str(p.value),
                    }
                    for p in promos
                ],
            }
        )


class BotWelcomeView(APIView):
    """Публичный endpoint для бота: текст + есть ли фото."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        s = ProgramSettings.get_solo()
        has_photo = bool(s.bot_welcome_photo)
        return Response(
            {
                "text": s.bot_welcome_text
                or "Добро пожаловать в Q Premium — программу лояльности магазинов одежды.",
                "has_photo": has_photo,
                "photo_url": "/api/v1/bot/welcome-photo" if has_photo else "",
            }
        )


class BotWelcomePhotoView(APIView):
    """Отдаёт файл приветствия с диска — без публичного HTTP к backend:8000."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        s = ProgramSettings.get_solo()
        if not s.bot_welcome_photo:
            return Response(status=404)
        try:
            fh = s.bot_welcome_photo.open("rb")
        except FileNotFoundError:
            return Response(status=404)
        name = s.bot_welcome_photo.name or "welcome.jpg"
        content_type = "image/jpeg"
        lower = name.lower()
        if lower.endswith(".png"):
            content_type = "image/png"
        elif lower.endswith(".webp"):
            content_type = "image/webp"
        elif lower.endswith(".gif"):
            content_type = "image/gif"
        resp = FileResponse(fh, content_type=content_type)
        resp["Cache-Control"] = "public, max-age=3600"
        return resp


class ClientLookupView(APIView):
    permission_classes = [IsStore]
    throttle_classes = [LookupRateThrottle]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        client = Client.objects.by_phone(phone).first()
        if not client:
            raise EngineError("not_found", "Клиент не найден", 404)
        data = {
            "id": str(client.id),
            "full_name": client.full_name,
            "phone": client.phone,
            "balance": balance_breakdown(client.id),
        }
        return Response(data)


class AccrualCreateView(APIView):
    permission_classes = [IsStore]

    def post(self, request):
        if "points" in request.data:
            raise EngineError("points_not_allowed", "Кассир не передаёт points", 400)
        client = get_object_or_404(Client, pk=request.data.get("client_id"))
        amount = _dec(request.data.get("purchase_amount"))
        key = request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
        if not key:
            raise EngineError("validation_error", "Нужен Idempotency-Key", 400)
        store = _resolve_store_for_write(request)
        op = create_accrual(
            client=client,
            purchase_amount=amount,
            store=store,
            operator_telegram_id=request.actor.telegram_id,
            idempotency_key=key,
        )
        _audit(request, "ACCRUAL_CREATED", "operation", op.id, {"points": op.points})

        # ADMIN: начисление сразу подтверждается (без очереди)
        if request.actor.role == "ADMIN" and op.status == Operation.Status.PENDING:
            op = confirm_accrual(op)
            _audit(request, "ACCRUAL_APPROVED", "operation", op.id, {"auto": True, "by": "admin"})
            bal = balance_breakdown(op.client_id)
            notify_client_after_confirm(op, bal["total"])

        return Response(_op_json(op), status=201)


class RedemptionPreviewView(APIView):
    permission_classes = [IsStore]

    def post(self, request):
        client = get_object_or_404(Client, pk=request.data.get("client_id"))
        amount = _dec(request.data.get("purchase_amount"))
        return Response(preview_redemption(client=client, purchase_amount=amount))


class RedemptionCreateView(APIView):
    permission_classes = [IsStore]

    def post(self, request):
        if "points" in request.data:
            raise EngineError("points_not_allowed", "Кассир не передаёт points", 400)
        client = get_object_or_404(Client, pk=request.data.get("client_id"))
        amount = _dec(request.data.get("purchase_amount"))
        key = request.headers.get("Idempotency-Key") or request.data.get("idempotency_key")
        if not key:
            raise EngineError("validation_error", "Нужен Idempotency-Key", 400)
        store = _resolve_store_for_write(request)
        op, to_redeem = apply_redemption(
            client=client,
            purchase_amount=amount,
            store=store,
            operator_telegram_id=request.actor.telegram_id,
            idempotency_key=key,
        )
        _audit(request, "REDEMPTION_CREATED", "operation", op.id, {"points": op.points})
        bal = balance_breakdown(client.id)
        notify_client_after_redeem(op, bal["total"])
        return Response(
            {
                "operation": _op_json(op),
                "to_redeem": to_redeem,
                "allocations": [
                    {"lot_id": str(a.lot_id), "points": a.points} for a in op.allocations.all()
                ],
                "balance_after": bal,
            },
            status=201,
        )


class PendingListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        ops = Operation.objects.filter(
            type=Operation.Type.BONUS_ACCRUAL, status=Operation.Status.PENDING
        ).order_by("created_at")
        return Response({"count": ops.count(), "page": 1, "page_size": 100, "results": [_op_json(o) for o in ops[:100]]})


class OperationConfirmView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        op = get_object_or_404(Operation, pk=pk)
        op = confirm_accrual(op)
        _audit(request, "ACCRUAL_APPROVED", "operation", op.id)
        bal = balance_breakdown(op.client_id)
        notify_client_after_confirm(op, bal["total"])
        return Response(_op_json(op))


class OperationRejectView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        op = get_object_or_404(Operation, pk=pk)
        reason = (request.data.get("reason") or "").strip()
        op = reject_accrual(op, reason=reason)
        _audit(request, "ACCRUAL_REJECTED", "operation", op.id, {"reason": reason})
        notify_client_after_reject(op, reason=reason)
        return Response(_op_json(op))


class AdminClientDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        bal = balance_breakdown(client.id)
        return Response(
            {
                "id": str(client.id),
                "full_name": client.full_name,
                "phone": client.phone,
                "email": client.email,
                "birth_date": str(client.birth_date),
                "telegram_id": client.telegram_id,
                "status": client.status,
                "registered_at": to_moscow_iso(client.registered_at),
                "registered_at_display": format_moscow_dt(client.registered_at),
                "balance": bal,
                "balance_display": {
                    "total": bal["total"],
                    "earned": bal["earned"],
                    "gift": bal["gift"],
                    "earned_label": "накопительные",
                    "gift_label": "подарочные",
                },
                "consents": consent_proof_summary(client),
                "consents_display": consents_for_display(client),
            }
        )

    def patch(self, request, pk):
        """ADMIN может менять ДР сразу (без очереди подтверждения)."""
        client = get_object_or_404(Client, pk=pk)
        for field in ("full_name", "email"):
            if field in request.data:
                setattr(client, field, str(request.data[field]).strip())
        if "phone" in request.data:
            client.phone = normalize_phone(request.data["phone"])
        if "email" in request.data:
            client.email = str(request.data["email"]).strip().lower()
        if "birth_date" in request.data:
            try:
                client.birth_date = date_cls.fromisoformat(str(request.data["birth_date"]))
            except (TypeError, ValueError) as exc:
                raise EngineError("validation_error", "Некорректная дата рождения", 400) from exc
            ProfileChangeRequest.objects.filter(
                client=client,
                field="birth_date",
                status=ProfileChangeRequest.Status.PENDING,
            ).update(
                status=ProfileChangeRequest.Status.APPROVED,
                decided_at=timezone.now(),
                decided_by_telegram_id=request.actor.telegram_id,
                comment="Изменено администратором напрямую",
            )
        client.save()
        _audit(request, "CLIENT_UPDATED_BY_ADMIN", "client", client.id)
        return self.get(request, pk)


def _resolve_store_for_write(request) -> Store:
    actor = request.actor
    if actor.role == "STORE":
        if request.data.get("store_id") and str(request.data.get("store_id")) != actor.store_id:
            raise EngineError("forbidden", "Нельзя подменить store_id", 403)
        return get_object_or_404(Store, pk=actor.store_id, is_active=True)
    store_id = request.data.get("store_id")
    if not store_id:
        raise EngineError("validation_error", "ADMIN обязан указать store_id", 400)
    return get_object_or_404(Store, pk=store_id, is_active=True)


def _op_json(op: Operation) -> dict:
    point_type_label = {
        "earned": "накопительные",
        "gift": "подарочные",
        "mixed": "смешанные",
    }.get(op.point_type or "", op.point_type or "")
    return {
        "id": str(op.id),
        "client_id": str(op.client_id),
        "type": op.type,
        "status": op.status,
        "purchase_amount": str(op.purchase_amount) if op.purchase_amount is not None else None,
        "points": op.points,
        "point_type": op.point_type,
        "point_type_label": point_type_label,
        "store_id": str(op.store_id) if op.store_id else None,
        "store_name_snapshot": op.store_name_snapshot,
        "store_address_snapshot": op.store_address_snapshot,
        "operator_telegram_id": op.operator_telegram_id,
        "operator_name_snapshot": op.operator_name_snapshot
        or (resolve_operator_name(op.operator_telegram_id) if op.operator_telegram_id else ""),
        "created_at": to_moscow_iso(op.created_at),
        "created_at_display": format_moscow_dt(op.created_at),
        "decided_at": to_moscow_iso(op.decided_at) if op.decided_at else None,
    }
