from django.contrib import admin

from loyalty.models import BonusLot, Operation, ProgramSettings


admin.site.register(ProgramSettings)
admin.site.register(Operation)
admin.site.register(BonusLot)
