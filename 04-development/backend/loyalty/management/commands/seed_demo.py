from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from loyalty.models import LoyaltyRule, StaffProfile, Store


class Command(BaseCommand):
    help = "Магазины 1–4, правило 10%, админ и кассир. Только локальная разработка."

    def handle(self, *args, **options):
        stores = []
        for i in range(1, 5):
            store, _ = Store.objects.get_or_create(
                code=f"store-{i}",
                defaults={"name": f"Магазин {i}"},
            )
            stores.append(store)
        LoyaltyRule.objects.update_or_create(pk=1, defaults={"percent": Decimal("10.00")})

        admin, created = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        if created or not admin.has_usable_password():
            admin.set_password("devpass")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
        StaffProfile.objects.update_or_create(
            user=admin,
            defaults={"role": StaffProfile.ROLE_ADMIN, "store": None},
        )

        cashier, created = User.objects.get_or_create(username="cashier1")
        if created or not cashier.has_usable_password():
            cashier.set_password("devpass")
            cashier.save()
        StaffProfile.objects.update_or_create(
            user=cashier,
            defaults={"role": StaffProfile.ROLE_CASHIER, "store": stores[0]},
        )
        self.stdout.write(self.style.SUCCESS("OK: магазины 1–4, правило 10%, admin/cashier1 пароль devpass (только local)"))
