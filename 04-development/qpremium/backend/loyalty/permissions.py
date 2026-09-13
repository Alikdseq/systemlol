from rest_framework.permissions import BasePermission


class IsTelegramAuthenticated(BasePermission):
    message = "Нужна авторизация. Закройте Mini App и откройте снова."

    def has_permission(self, request, view):
        return bool(getattr(request, "actor", None) or getattr(request.user, "telegram_id", None))


class RolePermission(BasePermission):
    allowed: tuple[str, ...] = ()

    def has_permission(self, request, view):
        actor = getattr(request, "actor", None)
        if not actor:
            return False
        return actor.role in self.allowed


class IsNoneRole(RolePermission):
    allowed = ("NONE",)


class CanRegister(BasePermission):
    """Регистрация профиля клиента, если Client ещё нет (в т.ч. для кассира/админа)."""

    message = "Профиль клиента уже есть или нет авторизации"

    def has_permission(self, request, view):
        actor = getattr(request, "actor", None)
        if not actor:
            return False
        return actor.client_id is None


class IsClient(BasePermission):
    """Свой клиентский профиль: роль CLIENT или STORE/ADMIN с client_id."""

    message = "Нужен профиль клиента"

    def has_permission(self, request, view):
        actor = getattr(request, "actor", None)
        if not actor:
            return False
        if actor.role == "CLIENT":
            return True
        return bool(actor.client_id and actor.role in ("STORE", "ADMIN"))


class IsStore(RolePermission):
    allowed = ("STORE", "ADMIN")


class IsAdmin(RolePermission):
    allowed = ("ADMIN",)


class IsStoreOnly(RolePermission):
    allowed = ("STORE",)
