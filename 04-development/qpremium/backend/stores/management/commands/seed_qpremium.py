from django.core.management.base import BaseCommand
from django.db import IntegrityError

from loyalty.models import ProgramSettings
from stores.models import AdminUser


class Command(BaseCommand):
    help = "Ensure program settings and optional admin. Does not create or delete stores."

    def add_arguments(self, parser):
        parser.add_argument("--admin-telegram-id", type=int, default=None)

    def handle(self, *args, **options):
        try:
            ProgramSettings.get_solo()
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"ProgramSettings: {exc}")

        admin_tg = options.get("admin_telegram_id")
        if admin_tg:
            try:
                AdminUser.objects.get_or_create(
                    telegram_id=admin_tg,
                    defaults={"is_active": True},
                )
                self.stdout.write(self.style.SUCCESS(f"ADMIN {admin_tg}"))
            except IntegrityError:
                self.stdout.write(self.style.SUCCESS(f"ADMIN {admin_tg} already exists"))

        self.stdout.write(self.style.SUCCESS("Seed OK (stores unchanged)"))
