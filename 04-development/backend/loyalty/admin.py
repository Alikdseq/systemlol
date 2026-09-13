from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Account, Client, LoyaltyRule, Operation, StaffProfile, Store


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (StaffProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Store)
admin.site.register(Client)
admin.site.register(Account)
admin.site.register(LoyaltyRule)
admin.site.register(Operation)
admin.site.register(StaffProfile)
