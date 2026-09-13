from django.core.management.base import BaseCommand

from loyalty.models import ProgramSettings
from stores.models import AdminUser, Store


class Command(BaseCommand):
    help = "Seed 4 stores, ProgramSettings, optional first ADMIN telegram_id"

    def add_arguments(self, parser):
        parser.add_argument("--admin-telegram-id", type=int, default=None)

    def handle(self, *args, **options):
        ProgramSettings.get_solo()
        defaults = [
            ("Магазин 1", "Адрес 1"),
            ("Магазин 2", "Адрес 2"),
            ("Магазин 3", "Адрес 3"),
            ("Магазин 4", "Адрес 4"),
        ]
        for name, address in defaults:
            Store.objects.get_or_create(name=name, defaults={"address": address, "is_active": True})
        admin_tg = options.get("admin_telegram_id")
        if admin_tg:
            AdminUser.objects.get_or_create(telegram_id=admin_tg, defaults={"is_active": True})
            self.stdout.write(self.style.SUCCESS(f"ADMIN {admin_tg}"))
        self.stdout.write(self.style.SUCCESS("Seed OK"))
