from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import exception_handler

from loyalty.engine import EngineError


def api_exception_handler(exc, context):
    request = context.get("request")
    request_id = getattr(request, "request_id", "") if request is not None else ""

    if isinstance(exc, EngineError):
        return _error(exc.code, exc.message, exc.http_status, request_id)

    if isinstance(exc, AuthenticationFailed):
        raw = str(exc.detail)
        code = raw if raw in ("token_expired", "invalid_init_data", "unauthorized") else "unauthorized"
        message = {
            "token_expired": "Сессия истекла. Закройте Mini App и откройте снова через бота.",
            "invalid_init_data": "Невалидные данные Telegram",
            "unauthorized": "Сессия недействительна. Закройте Mini App и откройте снова через бота.",
        }.get(code, raw)
        return _error(code, message, 401, request_id)

    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data
        if isinstance(detail, dict) and "detail" in detail:
            msg = str(detail["detail"])
        else:
            msg = str(detail)
        code = "validation_error" if response.status_code == 400 else "error"
        if response.status_code == 401:
            code = msg if msg in ("token_expired", "invalid_init_data", "unauthorized") else "unauthorized"
            if "учетные данные" in msg.lower() or "credentials" in msg.lower():
                msg = "Сессия не найдена. Закройте Mini App и откройте снова через бота."
        elif response.status_code == 403:
            code = "forbidden"
            if "permission" in msg.lower() or "прав" in msg.lower():
                msg = "Недостаточно прав для этого действия"
        elif response.status_code == 404:
            code = "not_found"
        request = context.get("request")
        response.data = {
            "error": {
                "code": code,
                "message": msg,
                "details": detail if isinstance(detail, dict) else {},
                "request_id": getattr(request, "request_id", ""),
            }
        }
    return response


def _error(code, message, status, request_id=""):
    from rest_framework.response import Response

    return Response(
        {"error": {"code": code, "message": message, "details": {}, "request_id": request_id}},
        status=status,
    )
