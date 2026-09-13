from django.contrib import admin

from stores.models import AdminUser, Store, StoreAccess

admin.site.register(Store)
admin.site.register(StoreAccess)
admin.site.register(AdminUser)
