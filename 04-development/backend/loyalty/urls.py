from django.urls import path

from . import views

app_name = "loyalty"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home"),
    path("cashier/", views.cashier_search, name="cashier_search"),
    path("cashier/create/", views.cashier_create, name="cashier_create"),
    path("cashier/client/<int:client_id>/", views.cashier_card, name="cashier_card"),
    path("office/clients/", views.office_clients, name="office_clients"),
    path("office/clients/<int:client_id>/", views.office_client, name="office_client"),
    path("office/rule/", views.office_rule, name="office_rule"),
]
