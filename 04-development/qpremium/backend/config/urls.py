import os

from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from legal import api as legal_api
from loyalty import admin_api, views

urlpatterns = [
    path("api/v1/health/", views.health),
    path("api/v1/legal", legal_api.LegalDocumentListView.as_view()),
    path("api/v1/legal/<slug:slug>", legal_api.LegalDocumentDetailView.as_view()),
    path("api/v1/auth/telegram", views.AuthTelegramView.as_view()),
    path("api/v1/auth/bot-resolve", views.BotResolveRoleView.as_view()),
    path("api/v1/auth/me", views.AuthMeView.as_view()),
    path("api/v1/clients/register", views.RegisterView.as_view()),
    path("api/v1/clients/me", views.ClientMeView.as_view()),
    path("api/v1/clients/me/advertising", views.ClientAdvertisingView.as_view()),
    path("api/v1/clients/me/balance", views.ClientBalanceView.as_view()),
    path("api/v1/clients/lookup", views.ClientLookupView.as_view()),
    path("api/v1/clients/export", admin_api.ClientExportView.as_view()),
    path("api/v1/clients", admin_api.ClientListView.as_view()),
    path("api/v1/clients/<uuid:pk>", views.AdminClientDetailView.as_view()),
    path("api/v1/clients/<uuid:pk>/operations", admin_api.ClientOperationsView.as_view()),
    path("api/v1/clients/<uuid:pk>/gifts", admin_api.ClientGiftView.as_view()),
    path("api/v1/clients/<uuid:pk>/adjustments", admin_api.ClientAdjustmentView.as_view()),
    path("api/v1/settings/public", views.PublicSettingsView.as_view()),
    path("api/v1/settings", admin_api.SettingsView.as_view()),
    path("api/v1/bot/welcome", views.BotWelcomeView.as_view()),
    path("api/v1/bot/welcome-photo", views.BotWelcomePhotoView.as_view()),
    path("api/v1/accruals", views.AccrualCreateView.as_view()),
    path("api/v1/redemptions/preview", views.RedemptionPreviewView.as_view()),
    path("api/v1/redemptions", views.RedemptionCreateView.as_view()),
    path("api/v1/operations/pending", views.PendingListView.as_view()),
    path("api/v1/operations", admin_api.OperationsListView.as_view()),
    path("api/v1/operations/<uuid:pk>", admin_api.OperationDetailView.as_view()),
    path("api/v1/operations/<uuid:pk>/confirm", views.OperationConfirmView.as_view()),
    path("api/v1/operations/<uuid:pk>/reject", views.OperationRejectView.as_view()),
    path("api/v1/stores", admin_api.StoreListCreateView.as_view()),
    path("api/v1/stores/<uuid:pk>", admin_api.StorePatchView.as_view()),
    path("api/v1/store-accesses", admin_api.StoreAccessListCreateView.as_view()),
    path("api/v1/store-accesses/<uuid:pk>", admin_api.StoreAccessPatchView.as_view()),
    path("api/v1/admins", admin_api.AdminListCreateView.as_view()),
    path("api/v1/admins/<uuid:pk>", admin_api.AdminPatchView.as_view()),
    path("api/v1/statistics", admin_api.StatisticsView.as_view()),
    path("api/v1/broadcasts", admin_api.BroadcastListCreateView.as_view()),
    path("api/v1/promotions", admin_api.PromotionListCreateView.as_view()),
    path("api/v1/promotions/<uuid:pk>", admin_api.PromotionDetailView.as_view()),
    path("api/v1/profile-changes/pending", admin_api.ProfileChangePendingView.as_view()),
    path("api/v1/profile-changes/<uuid:pk>/decide", admin_api.ProfileChangeDecideView.as_view()),
    path("api/v1/backups", admin_api.BackupCreateView.as_view()),
    path("api/v1/backups/latest/download", admin_api.BackupDownloadView.as_view()),
]

# Django /admin/ — только DEBUG или явный ENABLE_DJANGO_ADMIN=1 (не для публичного prod)
if settings.DEBUG or os.getenv("ENABLE_DJANGO_ADMIN", "0") == "1":
    from django.contrib import admin

    urlpatterns = [path("admin/", admin.site.urls), *urlpatterns]

# Welcome/media files must be reachable for the bot even when DEBUG=0.
# django.conf.urls.static.static() is a no-op outside DEBUG.
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
