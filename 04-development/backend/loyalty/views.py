from decimal import Decimal, InvalidOperation
import uuid

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_POST

from .models import Client, LoyaltyRule, Operation, StaffProfile, Store
from . import services


def _profile(request):
    try:
        return request.user.staff_profile
    except StaffProfile.DoesNotExist:
        return None


def _require_profile(request):
    profile = _profile(request)
    if profile is None:
        logout(request)
        messages.error(request, "У пользователя нет роли кассира или админа.")
        return None
    return profile


def login_view(request):
    if request.user.is_authenticated:
        return redirect("loyalty:home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("loyalty:home")
    return render(request, "loyalty/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("loyalty:login")


@login_required
def home(request):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if profile.is_admin():
        return redirect("loyalty:office_clients")
    return redirect("loyalty:cashier_search")


@login_required
@require_http_methods(["GET", "POST"])
def cashier_search(request):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if not profile.is_cashier() or not profile.store_id:
        return render(request, "loyalty/forbidden.html", status=403)

    if request.method == "POST":
        phone = request.POST.get("phone", "")
        try:
            client = services.lookup_client(phone)
            return redirect("loyalty:cashier_card", client_id=client.id)
        except services.DomainError as exc:
            if exc.code == "not_found":
                return render(
                    request,
                    "loyalty/cashier_search.html",
                    {
                        "store": profile.store,
                        "phone": phone,
                        "not_found": True,
                        "error": None,
                    },
                )
            return render(
                request,
                "loyalty/cashier_search.html",
                {"store": profile.store, "phone": phone, "error": str(exc)},
            )
    return render(request, "loyalty/cashier_search.html", {"store": profile.store})


@login_required
@require_http_methods(["POST"])
def cashier_create(request):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if not profile.is_cashier():
        return render(request, "loyalty/forbidden.html", status=403)
    try:
        client = services.create_client(request.POST.get("phone", ""))
        messages.success(request, "Клиент создан." if client.account.balance_bonus == 0 else "Клиент уже был в базе.")
        return redirect("loyalty:cashier_card", client_id=client.id)
    except services.DomainError as exc:
        messages.error(request, str(exc))
        return redirect("loyalty:cashier_search")


@login_required
@require_http_methods(["GET", "POST"])
def cashier_card(request, client_id):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if not profile.is_cashier() or not profile.store_id:
        return render(request, "loyalty/forbidden.html", status=403)

    client = get_object_or_404(Client.objects.select_related("account"), pk=client_id)
    preview_percent = None
    try:
        preview_percent = services.get_rule().percent
    except services.DomainError:
        preview_percent = None

    if request.method == "POST":
        action = request.POST.get("action")
        key = request.POST.get("idempotency_key") or str(uuid.uuid4())
        try:
            amount = Decimal(request.POST.get("check_amount_rub", "0").replace(",", "."))
        except (InvalidOperation, TypeError):
            messages.error(request, "Некорректная сумма чека.")
            return redirect("loyalty:cashier_card", client_id=client.id)
        try:
            if action == "accrual":
                op = services.accrue(
                    client=client,
                    store=profile.store,
                    staff=request.user,
                    check_amount=amount,
                    idempotency_key=key,
                )
                client.account.refresh_from_db()
                messages.success(
                    request,
                    f"Начислено {op.amount_bonus} бонусов. Баланс: {client.account.balance_bonus}.",
                )
            elif action == "redeem":
                bonus = int(request.POST.get("bonus_to_redeem") or "0")
                op = services.redeem(
                    client=client,
                    store=profile.store,
                    staff=request.user,
                    check_amount=amount,
                    bonus_to_redeem=bonus,
                    idempotency_key=key,
                )
                client.account.refresh_from_db()
                cash = amount - Decimal(bonus)
                messages.success(
                    request,
                    f"Списано {bonus} бонусов. В 1С пробейте скидку {bonus} руб. "
                    f"К оплате живыми: {cash} руб. Баланс: {client.account.balance_bonus}.",
                )
            else:
                messages.error(request, "Неизвестное действие.")
        except services.DomainError as exc:
            messages.error(request, str(exc))
        except ValueError:
            messages.error(request, "Количество бонусов должно быть целым числом.")
        return redirect("loyalty:cashier_card", client_id=client.id)

    recent = client.operations.select_related("store")[:10]
    return render(
        request,
        "loyalty/cashier_card.html",
        {
            "client": client,
            "store": profile.store,
            "phone_fmt": services.format_phone(client.phone),
            "preview_percent": preview_percent,
            "idempotency_key": str(uuid.uuid4()),
            "recent": recent,
        },
    )


@login_required
def office_clients(request):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if not profile.is_admin():
        return render(request, "loyalty/forbidden.html", status=403)

    qs = Client.objects.select_related("account").order_by("-created_at")
    phone = request.GET.get("phone", "").strip()
    if phone:
        try:
            qs = qs.filter(phone=services.normalize_phone(phone))
        except services.DomainError:
            qs = qs.none()
            messages.error(request, "Некорректный телефон для поиска.")
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "loyalty/office_clients.html", {"page": page, "phone": phone})


@login_required
@require_http_methods(["GET", "POST"])
def office_client(request, client_id):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if not profile.is_admin():
        return render(request, "loyalty/forbidden.html", status=403)

    client = get_object_or_404(Client.objects.select_related("account"), pk=client_id)

    if request.method == "POST" and request.POST.get("action") == "adjust":
        try:
            delta = int(request.POST.get("delta") or "0")
            store_id = request.POST.get("store_id") or None
            store = Store.objects.filter(pk=store_id).first() if store_id else None
            services.adjust(
                client=client,
                staff=request.user,
                delta=delta,
                comment=request.POST.get("comment", ""),
                store=store,
            )
            client.account.refresh_from_db()
            messages.success(request, f"Баланс изменён. Сейчас: {client.account.balance_bonus}.")
        except (services.DomainError, ValueError) as exc:
            messages.error(request, str(exc))
        return redirect("loyalty:office_client", client_id=client.id)

    ops = client.operations.select_related("store", "staff")
    store_id = request.GET.get("store_id")
    date_from = parse_date(request.GET.get("date_from") or "")
    date_to = parse_date(request.GET.get("date_to") or "")
    if store_id:
        ops = ops.filter(store_id=store_id)
    if date_from:
        ops = ops.filter(created_at__date__gte=date_from)
    if date_to:
        ops = ops.filter(created_at__date__lte=date_to)

    return render(
        request,
        "loyalty/office_client.html",
        {
            "client": client,
            "phone_fmt": services.format_phone(client.phone),
            "operations": ops[:200],
            "stores": Store.objects.filter(is_active=True),
            "filter_store_id": store_id or "",
            "filter_date_from": request.GET.get("date_from") or "",
            "filter_date_to": request.GET.get("date_to") or "",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def office_rule(request):
    profile = _require_profile(request)
    if profile is None:
        return redirect("loyalty:login")
    if not profile.is_admin():
        return render(request, "loyalty/forbidden.html", status=403)

    rule, _ = LoyaltyRule.objects.get_or_create(pk=1, defaults={"percent": Decimal("10.00")})
    if request.method == "POST":
        try:
            percent = Decimal(request.POST.get("percent", "").replace(",", "."))
            if percent < 0 or percent > 100:
                raise InvalidOperation
            rule.percent = percent
            rule.save()
            messages.success(request, "Правило сохранено. Старые операции не пересчитываются.")
            return redirect("loyalty:office_rule")
        except (InvalidOperation, TypeError):
            messages.error(request, "Процент должен быть числом от 0 до 100.")
    return render(request, "loyalty/office_rule.html", {"rule": rule})
